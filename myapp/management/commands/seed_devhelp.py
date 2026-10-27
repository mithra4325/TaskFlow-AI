from django.core.management.base import BaseCommand
from myapp.models import FAQ, ErrorCode


class Command(BaseCommand):
    help = "Seed realistic software-development FAQs and standard Error Codes for DevHelp AI."

    def handle(self, *args, **options):
        self.stdout.write("Seeding DevHelp AI FAQs and Error Codes...")

        faqs = [
            # Category: Getting Started
            {
                "question": "What is TaskFlow AI?",
                "answer": "TaskFlow AI is a task management web application that helps users organize tasks, track their completion, and access application help through an AI assistant. It also provides FAQs, an error code guide, and a support system.",
                "category": FAQ.Category.GETTING_STARTED,
                "keywords": "TaskFlow AI, overview, tasks, help",
            },
            {
                "question": "How do I create a new task?",
                "answer": "Open the My Tasks page and use the task creation form to enter the task details. Submit the form to save the task. The task will immediately appear in your task list and update your completion progress.",
                "category": FAQ.Category.GETTING_STARTED,
                "keywords": "create task, add task, new task, My Tasks",
            },
            {
                "question": "How do I mark a task as completed?",
                "answer": "Find the task in your task list on the My Tasks or Dashboard page and use its completion checkbox or Done button. The task's completion status updates immediately and remains saved in the database when you revisit or refresh the page.",
                "category": FAQ.Category.GETTING_STARTED,
                "keywords": "complete task, task status, checkbox, progress",
            },

            # Category: Tasks & Categories
            {
                "question": "Can I delete a task?",
                "answer": "Yes. On the My Tasks page, locate the relevant task and click its delete trash icon. A browser confirmation dialog will ask you to confirm deletion. Once confirmed, the task is permanently removed from the database.",
                "category": FAQ.Category.TASKS_CATEGORIES,
                "keywords": "delete task, remove task, task management",
            },
            {
                "question": "What are categories used for?",
                "answer": "Categories (such as Work, Study, Personal, and Other) help users group and organize related tasks. You can assign a category when creating or editing any task, and review progress and task counts by category on the Categories page.",
                "category": FAQ.Category.TASKS_CATEGORIES,
                "keywords": "categories, organize tasks, task grouping",
            },
            {
                "question": "Will my tasks remain saved when I leave the website?",
                "answer": "Yes. Tasks saved to the application are stored in the SQL database (SQLite locally or PostgreSQL in production) and persist when you navigate away, refresh, or reopen the website.",
                "category": FAQ.Category.TASKS_CATEGORIES,
                "keywords": "save tasks, persistence, database, task history",
            },

            # Category: AI Assistant
            {
                "question": "What can the AI assistant help me with?",
                "answer": "The AI assistant helps users understand the application's features, find answers to FAQs, and troubleshoot supported error codes (such as 400, 404, 500, or DEV001). It can also guide you on when and how to submit a support ticket.",
                "category": FAQ.Category.AI_ASSISTANT,
                "keywords": "AI assistant, chatbot, help, troubleshooting",
            },
            {
                "question": "What happens when the AI assistant cannot answer my question?",
                "answer": "If the assistant cannot find a reliable answer, it explains that limitation and offers you a direct way to raise a support ticket on the Support page so a developer can review your issue.",
                "category": FAQ.Category.AI_ASSISTANT,
                "keywords": "AI limitations, support ticket, unanswered question",
            },
            {
                "question": "Are my conversations with the AI assistant stored?",
                "answer": "The application logs assistant conversations to MongoDB in the 'conversations' collection when MongoDB is configured. Recorded data includes your session identifier, message text, assistant response, source references, and timestamp for diagnostic and support review.",
                "category": FAQ.Category.AI_ASSISTANT,
                "keywords": "chat history, MongoDB, data storage, privacy",
            },

            # Category: Troubleshooting & Support
            {
                "question": "What should I do if a page does not load or shows an error?",
                "answer": "Refresh the page and check whether the URL is correct. If the issue continues, consult the Error Code Guide (/errors/) for troubleshooting steps on the displayed error code (such as 404, 500, or DEV001). You can also ask the assistant for help or contact support.",
                "category": FAQ.Category.TROUBLESHOOTING_SUPPORT,
                "keywords": "page error, troubleshooting, error guide, website issue",
            },
            {
                "question": "How do I submit a support ticket?",
                "answer": "Open the Support page (/support/) and complete the available ticket form with a subject and description of your problem (name, email, and error code are optional). Submit the form and you will receive a unique reference code (e.g., TICK-123456) to track your ticket status anytime.",
                "category": FAQ.Category.TROUBLESHOOTING_SUPPORT,
                "keywords": "support, ticket, report a problem, help",
            },
            {
                "question": "What happens to the feedback I submit?",
                "answer": "Feedback submitted through the AI assistant is stored in MongoDB in the 'feedback' collection along with your session identifier and timestamp so it can be reviewed to improve assistant accuracy and application reliability.",
                "category": FAQ.Category.TROUBLESHOOTING_SUPPORT,
                "keywords": "feedback, MongoDB, suggestions, improvement",
            },
        ]

        # Update existing records in-place rather than inserting duplicates
        existing_faqs = list(FAQ.objects.order_by('id'))
        for idx, data in enumerate(faqs):
            if idx < len(existing_faqs):
                faq_obj = existing_faqs[idx]
                faq_obj.question = data["question"]
                faq_obj.answer = data["answer"]
                faq_obj.category = data["category"]
                faq_obj.keywords = data["keywords"]
                faq_obj.is_published = True
                faq_obj.save()
            else:
                FAQ.objects.create(
                    question=data["question"],
                    answer=data["answer"],
                    category=data["category"],
                    keywords=data["keywords"],
                    is_published=True,
                )

        # Delete any superfluous records beyond the 12
        if len(existing_faqs) > len(faqs):
            for extra in existing_faqs[len(faqs):]:
                extra.delete()

        self.stdout.write(self.style.SUCCESS(f"Successfully updated exactly {len(faqs)} FAQs in SQL database."))

        error_codes = [
            {
                "code": "400",
                "title": "Bad Request",
                "status_code": 400,
                "description": "The server could not understand or process the request due to invalid client syntax, malformed request routing, or deceptive request routing.",
                "common_causes": "• Malformed JSON payload in POST/PUT request\n• Missing required form fields or parameter validation failure\n• Corrupted cookies or oversized request headers\n• Invalid query parameters or malformed characters in URL",
                "troubleshooting_steps": "1. Inspect browser Network tab to view the exact payload sent in the request body.\n2. Check server-side logs to see which form field or JSON parser rejected the request.\n3. Verify Content-Type headers match the body format (e.g. application/json).\n4. Clear browser cookies and cache for the domain.",
                "suggested_fixes": "• Validate user input with Django forms or serializers before submission.\n• Ensure frontend fetch/axios calls set 'Content-Type: application/json' and serialize with JSON.stringify().\n• Implement clean error messages pinpointing exactly which field failed validation.",
            },
            {
                "code": "401",
                "title": "Unauthorized",
                "status_code": 401,
                "description": "The client request lacks valid authentication credentials for the requested target resource.",
                "common_causes": "• Missing Authorization header in API requests\n• Expired, revoked, or invalid JWT or OAuth token\n• Session cookie expired or cleared\n• Incorrect username or password on login endpoints",
                "troubleshooting_steps": "1. Check if the Authorization header is present (e.g. 'Bearer <token>').\n2. Verify session expiration time in Django settings (SESSION_COOKIE_AGE).\n3. Test authentication credentials directly via curl or Postman.",
                "suggested_fixes": "• Refresh expired access tokens using a refresh token workflow.\n• Redirect unauthenticated users to the login view with a 'next' redirect URL parameter.\n• Ensure the frontend includes credentials in fetch requests ('credentials: same-origin').",
            },
            {
                "code": "403",
                "title": "Forbidden",
                "status_code": 403,
                "description": "The server understood the client's identity, but refuses to authorize access. Unlike 401, re-authenticating will not grant permission.",
                "common_causes": "• Missing or invalid CSRF token on POST/PUT requests in Django\n• Insufficient permissions or role privileges (e.g. non-staff accessing /admin/)\n• File system permission restrictions on the web server\n• IP address whitelisting or firewall blocks",
                "troubleshooting_steps": "1. For Django web forms, confirm '{% csrf_token %}' is present inside the <form> tags.\n2. For AJAX/fetch requests, confirm 'X-CSRFToken' header is passed.\n3. Check user permissions using 'request.user.is_staff' or permission decorators.",
                "suggested_fixes": "• Add '{% csrf_token %}' to all POST templates.\n• Use Django's '@login_required' and '@permission_required' decorators appropriately.\n• Verify server directory permissions allow the web server user (www-data) to read static files.",
            },
            {
                "code": "404",
                "title": "Not Found",
                "status_code": 404,
                "description": "The server cannot find the requested URL path. It either does not exist, was moved, or was mistyped.",
                "common_causes": "• Typo in the URL address bar or frontend link\n• Missing URL pattern in 'urls.py' routing configuration\n• Database lookup failed (e.g. 'get_object_or_404' looking up a deleted or non-existent ID)\n• Trailing slash mismatch (e.g. requesting /about when route expects /about/)",
                "troubleshooting_steps": "1. Check the exact URL requested against 'myproject/urls.py' and 'myapp/urls.py'.\n2. Verify whether Django's APPEND_SLASH setting is affecting the request.\n3. Verify if the database ID exists in SQLite/PostgreSQL.",
                "suggested_fixes": "• Add missing path patterns in 'urls.py'.\n• Use Django's '{% url \"route_name\" %}' template tag instead of hardcoded link strings.\n• Provide a helpful custom 404 page with search links and a link back to homepage.",
            },
            {
                "code": "429",
                "title": "Too Many Requests",
                "status_code": 429,
                "description": "The user or client has sent too many requests in a given amount of time ('rate limiting').",
                "common_causes": "• Aggressive polling or infinite loops in frontend JavaScript\n• Third-party AI API quota limits exceeded (e.g. Google Gemini free tier quota)\n• Brute-force protection or anti-scraping middleware triggered",
                "troubleshooting_steps": "1. Check the 'Retry-After' response header to see how many seconds to wait.\n2. Review external API dashboard (e.g. Google AI Studio) to inspect quota usage.\n3. Check browser network tab for rapid repeated requests.",
                "suggested_fixes": "• Implement exponential backoff in retry logic.\n• Cache responses locally or in Redis to avoid redundant API calls.\n• Debounce user input on search bars and autocomplete fields (300ms–500ms).",
            },
            {
                "code": "500",
                "title": "Internal Server Error",
                "status_code": 500,
                "description": "The server encountered an unhandled exception or critical error that prevented it from fulfilling the request.",
                "common_causes": "• Unhandled Python exception (e.g. KeyError, TypeError, DatabaseError)\n• Database connection failure or unapplied migrations\n• Missing environment variable (e.g. GEMINI_API_KEY, SECRET_KEY)\n• Template syntax error or missing context variable",
                "troubleshooting_steps": "1. Check server terminal or log files for full Python tracebacks.\n2. In local development with DEBUG=True, inspect Django's interactive debug screen.\n3. Run 'python manage.py check' and 'python manage.py migrate'.",
                "suggested_fixes": "• Wrap risky operations (external API calls, file I/O) in try-except blocks with clean fallback handling.\n• Ensure all required environment variables are set in .env.\n• Provide a friendly, branded custom 500.html page in production so users are not stranded.",
            },
            {
                "code": "503",
                "title": "Service Unavailable",
                "status_code": 503,
                "description": "The server is currently unable to handle the request due to temporary maintenance or capacity overload.",
                "common_causes": "• Upstream service or external API is down or undergoing maintenance\n• Server CPU/memory exhaustion\n• Web application daemon (e.g. gunicorn) crashed and is restarting",
                "troubleshooting_steps": "1. Verify whether upstream services (Gemini API, database) are reachable.\n2. Check server resource consumption (CPU, RAM, disk space).\n3. Inspect deployment hosting status page.",
                "suggested_fixes": "• Set up health check endpoints (/health/) to monitor server readiness.\n• Implement graceful fallbacks so the app operates in offline mode when AI services are temporarily down.\n• Use a load balancer or process manager with automatic restart capabilities.",
            },
            {
                "code": "DEV001",
                "title": "AI Assistant Unavailable",
                "status_code": None,
                "description": "DevHelp AI custom site error: The Gemini AI Support Assistant service could not process the request.",
                "common_causes": "• GEMINI_API_KEY is missing or invalid in .env / environment\n• Google GenAI service connection timeout or network outage\n• AI quota limit reached for the current day/minute",
                "troubleshooting_steps": "1. Verify GEMINI_API_KEY is configured in your project .env file.\n2. Test outgoing internet connectivity from the server.\n3. Check server logs for GeminiServiceError details.",
                "suggested_fixes": "• The DevHelp AI site continues to function normally using the database FAQ and Error Guide.\n• Visitors can use the manual 'Ask a Question / Submit Ticket' form to submit their query to support.\n• Configure a valid GEMINI_API_KEY in the hosting environment variables.",
            },
        ]

        err_count = 0
        for data in error_codes:
            _, created = ErrorCode.objects.update_or_create(
                code=data["code"],
                defaults=data,
            )
            if created:
                err_count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully processed {len(error_codes)} Error Codes (created {err_count} new)."))
        self.stdout.write(self.style.SUCCESS("DevHelp AI seed complete!"))
