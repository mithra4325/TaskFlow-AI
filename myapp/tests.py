from datetime import date, timedelta
import json
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import FAQ, ErrorCode, SupportTicket, Task
from .ai_service import (
    retrieve_grounding_context,
    generate_support_assistant_response,
    is_gemini_configured,
)
from .mongo_service import log_chat_interaction, record_chat_feedback, check_mongo_connection
from .external_api import lookup_package_docs


class PortalPagesAndDatabaseTestCase(TestCase):
    """Test public web pages, database queries, and search/filtering."""

    def setUp(self):
        self.client = Client()
        # Seed test FAQs
        self.faq1 = FAQ.objects.create(
            question="What is Django?",
            answer="Django is a high-level Python web framework.",
            category=FAQ.Category.DJANGO,
            keywords="django, python, orm",
            is_published=True,
        )
        self.faq2 = FAQ.objects.create(
            question="What causes a 404 error?",
            answer="A 404 error means the requested URL was not found.",
            category=FAQ.Category.WEB_HTTP,
            keywords="404, routing, http",
            is_published=True,
        )
        # Seed test ErrorCodes
        self.ec_404 = ErrorCode.objects.create(
            code="404",
            title="Not Found",
            status_code=404,
            description="The requested page could not be located.",
            common_causes="Typo in URL or route missing.",
            troubleshooting_steps="Check urls.py.",
            suggested_fixes="Add path() to urls.py.",
        )
        self.ec_dev001 = ErrorCode.objects.create(
            code="DEV001",
            title="AI Assistant Unavailable",
            status_code=None,
            description="AI service connection timeout.",
            common_causes="Network drop or missing key.",
            troubleshooting_steps="Check .env configuration.",
            suggested_fixes="Add GEMINI_API_KEY in .env.",
        )

    def test_home_page_loads_with_database_records(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "TaskFlow")
        self.assertEqual(response.context['total_faqs'], 2)
        self.assertEqual(response.context['total_error_codes'], 2)

    def test_faq_list_and_search(self):
        # View all
        res = self.client.get(reverse('faq_list'))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context['total_count'], 2)

        # Search matching 'Django'
        res_search = self.client.get(reverse('faq_list') + '?q=Django')
        self.assertEqual(res_search.status_code, 200)
        self.assertEqual(res_search.context['total_count'], 1)
        self.assertContains(res_search, "What is Django?")
        self.assertNotContains(res_search, "What causes a 404 error?")

        # Filter by Category
        res_cat = self.client.get(reverse('faq_list') + '?category=Web%20%26%20HTTP')
        self.assertEqual(res_cat.status_code, 200)
        self.assertEqual(res_cat.context['total_count'], 1)
        self.assertContains(res_cat, "What causes a 404 error?")

    @patch('myapp.views.lookup_package_docs')
    def test_error_guide_and_detail(self, mock_lookup):
        mock_lookup.return_value = {
            'available': True,
            'source': 'local_fallback_catalog',
            'name': 'django',
            'version': '6.0+',
            'docs_url': 'https://docs.djangoproject.com/en/stable/',
            'home_page': 'https://www.djangoproject.com/',
        }
        res = self.client.get(reverse('error_guide'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "404")
        self.assertContains(res, "DEV001")

        # Detail view for 404
        detail_res = self.client.get(reverse('error_detail', args=['404']))
        self.assertEqual(detail_res.status_code, 200)
        self.assertContains(detail_res, "Not Found")
        self.assertContains(detail_res, "Check urls.py")

        # Non-existent error code returns 404
        missing_res = self.client.get(reverse('error_detail', args=['99999']))
        self.assertEqual(missing_res.status_code, 404)

    def test_about_page_renders_ticket_form(self):
        res = self.client.get(reverse('about'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Submit a Support Ticket")
        self.assertContains(res, "DevHelp AI")


class SupportTicketCreationTestCase(TestCase):
    """Test support ticket submission, spam prevention, and unique reference codes."""

    def setUp(self):
        self.client = Client()

    def test_valid_ticket_submission_via_web_form(self):
        response = self.client.post(reverse('about'), {
            'subject': 'Database connection drop',
            'description': 'Receiving operational error during high concurrency tests.',
            'name': 'Alex Developer',
            'email': 'alex@example.com',
            'related_error_code': '500',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(SupportTicket.objects.count(), 1)
        ticket = SupportTicket.objects.first()
        self.assertTrue(ticket.reference.startswith('TICK-'))
        self.assertEqual(ticket.subject, 'Database connection drop')
        self.assertEqual(ticket.status, SupportTicket.Status.OPEN)

    def test_ticket_submission_empty_description_fails(self):
        response = self.client.post(reverse('about'), {
            'subject': 'Incomplete ticket',
            'description': '   ',  # Empty description
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SupportTicket.objects.count(), 0)
        self.assertContains(response, "Description cannot be empty")

    def test_honeypot_spam_rejection(self):
        response = self.client.post(reverse('about'), {
            'subject': 'Spam subject',
            'description': 'Spam body text',
            'honey_field': 'I am a spam bot',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SupportTicket.objects.count(), 0)
        self.assertContains(response, "Spam request rejected")

    def test_direct_ticket_api_post(self):
        payload = {
            'subject': 'API Support Request',
            'description': 'Testing JSON ticket endpoint directly.',
            'name': 'API User',
        }
        res = self.client.post(
            reverse('ticket_create_api'),
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['reference'].startswith('TICK-'))
        self.assertEqual(SupportTicket.objects.count(), 1)


class DevHelpAIAssistantTestCase(TestCase):
    """Test database grounding, mocked Gemini AI answers, unknown-answer escalation, and offline fallback."""

    def setUp(self):
        self.client = Client()
        self.ec_404 = ErrorCode.objects.create(
            code="404",
            title="Not Found",
            description="The requested URL was not found.",
            common_causes="Incorrect path in urls.py.",
            troubleshooting_steps="Check urlpatterns.",
            suggested_fixes="Ensure route is registered.",
        )
        self.faq_migration = FAQ.objects.create(
            question="What is a database migration?",
            answer="A migration propagates model changes into database schema.",
            category=FAQ.Category.DATABASE,
            keywords="migration, schema, orm",
            is_published=True,
        )

    def test_retrieve_grounding_context(self):
        # Query about 404 should retrieve the 404 error code
        ctx_404 = retrieve_grounding_context("Why am I getting a 404 error on my page?")
        self.assertTrue(ctx_404['has_context'])
        self.assertIn(self.ec_404, ctx_404['error_codes'])

        # Query about migrations should retrieve the migration FAQ
        ctx_mig = retrieve_grounding_context("What does a migration do?")
        self.assertTrue(ctx_mig['has_context'])
        self.assertIn(self.faq_migration, ctx_mig['faqs'])

        # Unrelated query should return has_context = False
        ctx_none = retrieve_grounding_context("How do I bake a chocolate cake?")
        self.assertFalse(ctx_none['has_context'])

    @patch('myapp.ai_service.is_gemini_configured', return_value=True)
    @patch('myapp.ai_service.get_gemini_client')
    def test_gemini_grounded_response(self, mock_client, mock_cfg):
        mock_resp = MagicMock()
        mock_resp.text = "In Django, HTTP 404 means the requested route was not found in `urls.py`. Check your urlpatterns."
        mock_client.return_value.models.generate_content.return_value = mock_resp

        res = generate_support_assistant_response("Explain 404 error")
        self.assertTrue(res['has_grounding'])
        self.assertIn("404", res['reply'])
        self.assertFalse(res['escalated'])

    @patch('myapp.ai_service.is_gemini_configured', return_value=True)
    @patch('myapp.ai_service.get_gemini_client')
    def test_unknown_answer_suggests_support_ticket(self, mock_client, mock_cfg):
        mock_resp = MagicMock()
        mock_resp.text = "I could not find a verified answer for that in our knowledge base. Would you like me to open a support ticket for our engineering team?"
        mock_client.return_value.models.generate_content.return_value = mock_resp

        res = generate_support_assistant_response("How do I configure quantum computing in Python?")
        self.assertTrue(res['suggest_ticket'])
        self.assertFalse(res['ticket_created'])

    def test_user_agreement_creates_ticket_in_sql(self):
        """When user confirms ticket creation in chat, a SupportTicket record must be created."""
        history = [{'role': 'user', 'text': 'How do I deploy with Docker on Kubernetes?'}]
        res = generate_support_assistant_response("Yes, please create a ticket for me", conversation_history=history)

        self.assertTrue(res['ticket_created'])
        self.assertTrue(res['escalated'])
        self.assertIsNotNone(res['ticket_reference'])
        self.assertTrue(res['ticket_reference'].startswith('TICK-'))
        self.assertEqual(SupportTicket.objects.count(), 1)
        ticket = SupportTicket.objects.first()
        self.assertEqual(ticket.reference, res['ticket_reference'])

    @patch('myapp.ai_service.is_gemini_configured', return_value=False)
    def test_unconfigured_gemini_operates_in_local_knowledge_base_mode(self, mock_cfg):
        """When GEMINI_API_KEY is missing, assistant returns verified database answers without error."""
        res = generate_support_assistant_response("What causes a 404 error?")
        self.assertTrue(res['has_grounding'])
        self.assertIn("404", res['reply'])
        self.assertIn("Offline Knowledge Base Mode", res['reply'])


class MongoDBServiceAndFallbackTestCase(TestCase):
    """Verify MongoDB persistence and seamless fallback when MongoDB is unconfigured or offline."""

    @patch('myapp.mongo_service.get_mongo_db')
    def test_log_chat_interaction_success_with_mongodb(self, mock_db):
        mock_collection = MagicMock()
        mock_collection.insert_one.return_value.inserted_id = "mock_mongo_id_123"
        mock_db.return_value = ({'chat_logs': mock_collection}, None)

        success, log_id = log_chat_interaction("sess_1", "Hello", "Hi there!")
        self.assertTrue(success)
        self.assertEqual(log_id, "mock_mongo_id_123")

    @patch('myapp.mongo_service.get_mongo_db', return_value=(None, "MONGODB_URI unconfigured"))
    def test_log_chat_interaction_graceful_fallback_when_offline(self, mock_db):
        """Website and chat MUST continue working when MongoDB is offline."""
        success, err = log_chat_interaction("sess_2", "Query", "Answer")
        self.assertFalse(success)
        self.assertIn("MongoDB offline", err)

    @patch('myapp.mongo_service.get_mongo_db', return_value=(None, "Offline"))
    def test_feedback_api_graceful_fallback(self, mock_db):
        client = Client()
        res = client.post(
            reverse('chat_feedback_api'),
            data=json.dumps({
                'conversation_id': 'sess_3',
                'feedback_type': 'thumbs_up',
                'comment': 'Very helpful!'
            }),
            content_type='application/json',
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data['success'])  # Accurately reports persistence offline, doesn't crash


class ThirdPartyExternalAPITestCase(TestCase):
    """Test PyPI documentation API integration, timeouts, and curated local fallback catalog."""

    @patch('urllib.request.urlopen')
    def test_pypi_api_successful_lookup(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps({
            'info': {
                'name': 'django',
                'version': '6.1.0',
                'summary': 'The web framework for perfectionists with deadlines.',
                'project_urls': {'Documentation': 'https://docs.djangoproject.com/'},
                'home_page': 'https://www.djangoproject.com/'
            }
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        data = lookup_package_docs('django')
        self.assertTrue(data['available'])
        self.assertEqual(data['version'], '6.1.0')
        self.assertEqual(data['docs_url'], 'https://docs.djangoproject.com/')

    @patch('urllib.request.urlopen', side_effect=TimeoutError("Request timed out"))
    def test_pypi_api_timeout_uses_curated_local_fallback(self, mock_urlopen):
        """External network drop should gracefully fall back to local verified documentation index."""
        data = lookup_package_docs('django')
        self.assertTrue(data['available'])
        self.assertEqual(data['source'], 'local_fallback_catalog')
        self.assertIn('docs.djangoproject.com', data['docs_url'])


class HealthEndpointTestCase(TestCase):
    """Test machine-readable /health/ endpoint."""

    def test_health_check_returns_200_and_json(self):
        client = Client()
        res = client.get(reverse('health_check'))
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['services']['sql_database']['status'], 'connected')
        self.assertIn('sqlite', data['services']['sql_database']['engine'].lower())
        self.assertIn('mongodb', data['services'])
        self.assertIn('gemini_ai', data['services'])


class CustomErrorPagesTestCase(TestCase):
    """Verify custom error templates (400, 403, 404, 429, 500, 503) and genuine 404 / 500 behavior."""

    def setUp(self):
        self.client = Client()

    def test_genuinely_incorrect_url_returns_404_with_custom_template(self):
        response = self.client.get('/this-path-definitely-does-not-exist-xyz/')
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Page not found", status_code=404)
        self.assertContains(response, "HTTP 404", status_code=404)
        self.assertContains(response, "Go Home", status_code=404)
        self.assertContains(response, "Go Back", status_code=404)
        self.assertContains(response, "Ask Assistant", status_code=404)
        # Assistant widget must be present
        self.assertContains(response, 'id="devhelp-chat-widget"', status_code=404)
        self.assertContains(response, 'id="chat-launcher-btn"', status_code=404)

    def test_controlled_500_server_error_returns_custom_template(self):
        response = self.client.get('/demo-error/500/')
        self.assertEqual(response.status_code, 500)
        self.assertContains(response, "Something went wrong", status_code=500)
        self.assertContains(response, "HTTP 500", status_code=500)
        self.assertContains(response, "Try Again", status_code=500)
        self.assertContains(response, "Go Home", status_code=500)
        self.assertContains(response, "Ask Assistant", status_code=500)
        # Assistant widget must be present
        self.assertContains(response, 'id="devhelp-chat-widget"', status_code=500)
        self.assertContains(response, 'id="chat-launcher-btn"', status_code=500)

    def test_assistant_accessible_and_submits_message_from_error_pages(self):
        # 1. 404 page renders the functional chat widget
        res_404 = self.client.get('/nonexistent-page-404/')
        self.assertContains(res_404, 'chat-window', status_code=404)
        self.assertContains(res_404, 'chat-user-input', status_code=404)

        # 2. 500 page renders the functional chat widget
        res_500 = self.client.get('/demo-error/500/')
        self.assertContains(res_500, 'chat-window', status_code=500)
        self.assertContains(res_500, 'chat-user-input', status_code=500)

        # 3. Client can post questions via the chat API
        chat_res = self.client.post(
            reverse('chat_api'),
            data=json.dumps({'message': 'Explain error 404'}),
            content_type='application/json',
        )
        self.assertEqual(chat_res.status_code, 200)
        data = chat_res.json()
        self.assertIn('reply', data)

    def test_demo_error_pages_render(self):
        for code in ['400', '403', '404', '429', '500', '503']:
            res = self.client.get(f'/demo-error/{code}/')
            expected_status = int(code)
            self.assertEqual(res.status_code, expected_status)
            self.assertContains(res, f"HTTP {code}", status_code=expected_status)
            self.assertContains(res, "TaskFlow", status_code=expected_status)


class FAQApiTestCase(TestCase):
    """Test SQL-backed FAQ API endpoint (/api/faqs/)."""

    def setUp(self):
        self.client = Client()
        self.faq1 = FAQ.objects.create(
            question="How do I create a task?",
            answer="Go to My Tasks and submit the form.",
            category=FAQ.Category.GETTING_STARTED,
            keywords="create, task",
            is_published=True,
        )
        self.faq2 = FAQ.objects.create(
            question="What is TaskFlow AI?",
            answer="TaskFlow AI is a task management platform with an AI assistant.",
            category=FAQ.Category.GETTING_STARTED,
            keywords="overview",
            is_published=True,
        )

    def test_faq_api_returns_json_records(self):
        res = self.client.get(reverse('faq_api'))
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['status'], 'success')
        self.assertGreaterEqual(data['total_count'], 2)
        questions = [f['question'] for f in data['faqs']]
        self.assertIn("How do I create a task?", questions)

    def test_faq_api_filter_and_search(self):
        res = self.client.get(reverse('faq_api') + '?q=create')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['total_count'], 1)
        self.assertEqual(data['faqs'][0]['question'], "How do I create a task?")


class SupportTicketCRUDTestCase(TestCase):
    """Test ticket creation, lookup, ownership-based updates, and deletion."""

    def setUp(self):
        self.client = Client()

    def test_ticket_crud_lifecycle_with_authorization(self):
        # 1. Create Ticket via form
        post_res = self.client.post(reverse('support'), {
            'subject': 'Database latency on high loads',
            'description': 'Queries take more than 2 seconds.',
            'name': 'Test User',
            'email': 'user@example.com',
        })
        self.assertEqual(post_res.status_code, 302)
        ticket = SupportTicket.objects.filter(subject='Database latency on high loads').first()
        self.assertIsNotNone(ticket)
        # Check session ownership
        self.assertIn(ticket.reference, self.client.session.get('user_tickets', []))

        # 2. Read / Lookup Ticket
        lookup_res = self.client.get(f"{reverse('support')}?lookup_ref={ticket.reference}")
        self.assertEqual(lookup_res.status_code, 200)
        self.assertContains(lookup_res, ticket.reference)
        self.assertContains(lookup_res, "Edit Ticket")

        # 3. Update Ticket (Authorized)
        update_url = reverse('ticket_update', args=[ticket.reference])
        update_res = self.client.post(update_url, {
            'subject': 'Database latency resolved',
            'description': 'Added indexing, queries are fast now.',
            'status': SupportTicket.Status.RESOLVED,
        })
        self.assertEqual(update_res.status_code, 302)
        ticket.refresh_from_db()
        self.assertEqual(ticket.subject, 'Database latency resolved')
        self.assertEqual(ticket.status, SupportTicket.Status.RESOLVED)

        # 4. Update Ticket (Unauthorized from different client)
        other_client = Client()
        unauth_update = other_client.post(update_url, {
            'subject': 'Hacked subject',
            'description': 'Malicious modification',
        })
        self.assertEqual(unauth_update.status_code, 403)

        # 5. Delete Ticket (Unauthorized)
        delete_url = reverse('ticket_delete', args=[ticket.reference])
        unauth_delete = other_client.post(delete_url)
        self.assertEqual(unauth_delete.status_code, 403)
        self.assertTrue(SupportTicket.objects.filter(reference=ticket.reference).exists())

        # 6. Delete Ticket (Authorized)
        auth_delete = self.client.post(delete_url)
        self.assertEqual(auth_delete.status_code, 302)
        self.assertFalse(SupportTicket.objects.filter(reference=ticket.reference).exists())


class SecurityAndCSRFTestCase(TestCase):
    """Verify CSRF enforcement and security settings."""

    def test_csrf_protection_on_chat_api(self):
        csrf_client = Client(enforce_csrf_checks=True)
        # Direct POST without CSRF token must be rejected with 403 Forbidden
        res = csrf_client.post(
            reverse('chat_api'),
            data=json.dumps({'message': 'Hello'}),
            content_type='application/json',
        )
        self.assertEqual(res.status_code, 403)


class ProductivityAndMultiPageTestCase(TestCase):
    """Verify all 9 distinct pages, task CRUD, calendar navigation,
    category progress tracking, productivity insights, and AI coaching."""

    def setUp(self):
        self.client = Client()
        self.today = timezone.localdate()
        self.task_pending = Task.objects.create(
            title="Complete Django Assessment",
            description="Build multi-page application with AI assistant",
            priority=Task.Priority.HIGH,
            category=Task.Category.WORK,
            due_date=self.today + timedelta(days=2),
            estimated_duration=120,
            completed=False,
        )
        self.task_completed = Task.objects.create(
            title="Review Python documentation",
            description="Study generators and decorators",
            priority=Task.Priority.LOW,
            category=Task.Category.STUDY,
            due_date=self.today - timedelta(days=1),
            estimated_duration=45,
            completed=True,
        )
        self.task_overdue = Task.objects.create(
            title="Submit sprint backlog update",
            description="Past due status report",
            priority=Task.Priority.MEDIUM,
            category=Task.Category.WORK,
            due_date=self.today - timedelta(days=3),
            estimated_duration=30,
            completed=False,
        )

    def test_dashboard_page_statistics_and_focus(self):
        res = self.client.get(reverse('dashboard'))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context['total_tasks'], 3)
        self.assertEqual(res.context['completed_tasks'], 1)
        self.assertEqual(res.context['pending_tasks'], 2)
        self.assertEqual(res.context['overdue_count'], 1)
        self.assertEqual(res.context['progress_percentage'], 33)
        self.assertContains(res, "Complete Django Assessment")
        self.assertContains(res, "Submit sprint backlog update")

    def test_task_list_search_and_filter_parameters(self):
        # Filter pending
        res_pending = self.client.get(reverse('task_list') + '?filter=pending')
        self.assertEqual(res_pending.status_code, 200)
        self.assertIn(self.task_pending, res_pending.context['tasks'])
        self.assertNotIn(self.task_completed, res_pending.context['tasks'])

        # Filter overdue
        res_overdue = self.client.get(reverse('task_list') + '?filter=overdue')
        self.assertEqual(res_overdue.status_code, 200)
        self.assertIn(self.task_overdue, res_overdue.context['tasks'])
        self.assertNotIn(self.task_pending, res_overdue.context['tasks'])

        # Filter by category: study
        res_study = self.client.get(reverse('task_list') + '?category=study')
        self.assertEqual(res_study.status_code, 200)
        self.assertIn(self.task_completed, res_study.context['tasks'])
        self.assertNotIn(self.task_pending, res_study.context['tasks'])

        # Search by query: 'Django'
        res_search = self.client.get(reverse('task_list') + '?q=Django')
        self.assertEqual(res_search.status_code, 200)
        self.assertIn(self.task_pending, res_search.context['tasks'])
        self.assertNotIn(self.task_completed, res_search.context['tasks'])

    def test_categories_view_progress_calculation(self):
        res = self.client.get(reverse('categories'))
        self.assertEqual(res.status_code, 200)
        category_data = res.context['category_data']
        # Work category has 2 tasks: 1 pending, 1 overdue, 0 completed => 0% progress
        work_cat = next((c for c in category_data if c['key'] == 'work'), None)
        self.assertIsNotNone(work_cat)
        self.assertEqual(work_cat['total'], 2)
        self.assertEqual(work_cat['completed'], 0)
        self.assertEqual(work_cat['progress_percentage'], 0)

        # Study category has 1 task: 1 completed => 100% progress
        study_cat = next((c for c in category_data if c['key'] == 'study'), None)
        self.assertIsNotNone(study_cat)
        self.assertEqual(study_cat['total'], 1)
        self.assertEqual(study_cat['completed'], 1)
        self.assertEqual(study_cat['progress_percentage'], 100)

    def test_support_page_submission_and_status_lookup(self):
        # 1. Page renders form and lookup tool
        res = self.client.get(reverse('support'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Support")
        self.assertContains(res, "Check Ticket Status")

        # 2. Submit ticket via support page
        post_res = self.client.post(reverse('support'), {
            'subject': 'Database connection timeout',
            'description': 'Receiving operational error during peak hours.',
            'name': 'Test Engineer',
            'email': 'engineer@example.com',
            'related_error_code': '500',
        })
        self.assertEqual(post_res.status_code, 302)
        ticket = SupportTicket.objects.filter(subject='Database connection timeout').first()
        self.assertIsNotNone(ticket)

        # 3. Lookup ticket by reference
        lookup_res = self.client.get(f"{reverse('support')}?lookup_ref={ticket.reference}")
        self.assertEqual(lookup_res.status_code, 200)
        self.assertContains(lookup_res, ticket.reference)
        self.assertEqual(lookup_res.context['lookup_ticket'], ticket)

    @patch('myapp.ai_service.is_gemini_configured', return_value=False)
    def test_ai_assistant_productivity_guidance(self, mock_cfg):
        # In offline/local mode, query asking for task prioritization should receive productivity advice
        res = generate_support_assistant_response("How do I prioritize my tasks with the Eisenhower matrix?")
        self.assertTrue(res['has_grounding'])
        self.assertIn("Eisenhower Matrix", res['reply'])
        self.assertIn("TaskFlow Productivity Principles", res['reply'])
        self.assertFalse(res['suggest_ticket'])


