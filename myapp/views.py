"""Views for DevHelp AI - Developer Support Portal & AI Assistant.

Handles:
- Home: Portfolio overview, popular FAQs, common error codes, CTA
- FAQs: Categorized, searchable software development knowledge base
- Error Guide: Searchable HTTP & custom error code reference with troubleshooting steps
- Error Detail: Deep-dive error code explanation and suggested fixes
- About / Support: Website purpose, developer background, and support ticket submission
- Chat API: Database-grounded AI assistant endpoint with MongoDB logging
- Feedback API: Thumbs up/down feedback logging to MongoDB
- Health Endpoint: Machine-readable system readiness check
- Custom Error Handlers: 400, 403, 404, 500
- Preserved TaskFlow CRUD views for backward compatibility
"""

from datetime import datetime, date, timedelta, timezone as dt_timezone
import calendar
import json
import logging
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import connection
from django.db.models import Q, Sum, Count
from django.http import JsonResponse, HttpResponseNotFound, HttpResponseServerError
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST, require_GET

from .models import FAQ, ErrorCode, SupportTicket, Task
from .forms import TaskForm, DailyPlannerForm, SupportTicketForm
from .ai_service import (
    is_gemini_configured,
    generate_support_assistant_response,
    generate_task_breakdown,
    generate_daily_plan,
    GeminiError,
    DEFAULT_MODEL,
)
from .mongo_service import log_chat_interaction, record_chat_feedback, check_mongo_connection
from .external_api import lookup_package_docs

logger = logging.getLogger('devhelp.views')


# ==============================================================================
# 1. Dashboard Page
# ==============================================================================

@ensure_csrf_cookie
def dashboard(request):
    """1. Dashboard: Task statistics, completion progress, overdue tasks,
    upcoming deadlines, productivity overview, daily summary, and knowledge base highlights."""
    today = timezone.localdate()
    all_tasks = Task.objects.all()
    total_tasks = all_tasks.count()
    completed_tasks = all_tasks.filter(completed=True).count()
    pending_tasks = all_tasks.filter(completed=False).count()
    overdue_tasks = all_tasks.filter(completed=False, due_date__lt=today).order_by('due_date')
    overdue_count = overdue_tasks.count()

    # Upcoming deadlines within next 7 days
    next_week = today + timedelta(days=7)
    upcoming_tasks = all_tasks.filter(
        completed=False,
        due_date__gte=today,
        due_date__lte=next_week
    ).order_by('due_date')

    # Progress percentage
    progress_percentage = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0

    # Priority breakdown for pending tasks
    high_priority_count = all_tasks.filter(completed=False, priority=Task.Priority.HIGH).count()
    medium_priority_count = all_tasks.filter(completed=False, priority=Task.Priority.MEDIUM).count()
    low_priority_count = all_tasks.filter(completed=False, priority=Task.Priority.LOW).count()

    # Total estimated minutes remaining
    pending_minutes = all_tasks.filter(completed=False).aggregate(total=Sum('estimated_duration'))['total'] or 0
    estimated_hours_remaining = round(pending_minutes / 60, 1)

    # Focus task of the day
    focus_task = (
        overdue_tasks.first()
        or upcoming_tasks.filter(priority=Task.Priority.HIGH).first()
        or all_tasks.filter(completed=False).first()
    )

    # Recent tasks
    recent_tasks = all_tasks.order_by('-created_at')[:6]

    # Quick Add Form
    form = TaskForm()

    # Developer Support & Knowledge highlights
    featured_faqs = FAQ.objects.filter(is_published=True)[:4]
    featured_codes = ErrorCode.objects.filter(code__in=['400', '404', '500', 'DEV001'])
    if not featured_codes.exists():
        featured_codes = ErrorCode.objects.all()[:4]

    total_faqs = FAQ.objects.filter(is_published=True).count()
    total_error_codes = ErrorCode.objects.count()
    total_tickets = SupportTicket.objects.count()

    return render(request, 'myapp/dashboard.html', {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'overdue_count': overdue_count,
        'overdue_tasks': overdue_tasks[:4],
        'upcoming_tasks': upcoming_tasks[:5],
        'progress_percentage': progress_percentage,
        'high_priority_count': high_priority_count,
        'medium_priority_count': medium_priority_count,
        'low_priority_count': low_priority_count,
        'estimated_hours_remaining': estimated_hours_remaining,
        'focus_task': focus_task,
        'recent_tasks': recent_tasks,
        'today': today,
        'form': form,
        'featured_faqs': featured_faqs,
        'featured_codes': featured_codes,
        'total_faqs': total_faqs,
        'total_error_codes': total_error_codes,
        'total_tickets': total_tickets,
        'is_gemini_configured': is_gemini_configured(),
    })

# Backward compatibility alias for home
home = dashboard


# ==============================================================================
# 2. My Tasks Page (Full Task Management CRUD)
# ==============================================================================

@ensure_csrf_cookie
def task_list(request):
    """2. My Tasks: Full task management with add, edit, delete, completion status,
    priorities, due dates, categories, search, sorting, and filters."""
    today = timezone.localdate()
    base_qs = Task.objects.all()
    total_count = base_qs.count()
    completed_count = base_qs.filter(completed=True).count()
    pending_count = base_qs.filter(completed=False).count()
    overdue_count = base_qs.filter(completed=False, due_date__lt=today).count()
    progress_percentage = int((completed_count / total_count) * 100) if total_count > 0 else 0

    # Search
    search_query = request.GET.get('q', '').strip()
    if search_query:
        base_qs = base_qs.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )

    # Status filter
    filter_param = request.GET.get('filter', 'all').strip().lower()
    if filter_param == 'pending':
        base_qs = base_qs.filter(completed=False)
    elif filter_param == 'completed':
        base_qs = base_qs.filter(completed=True)
    elif filter_param == 'overdue':
        base_qs = base_qs.filter(completed=False, due_date__lt=today)

    # Category filter
    category_param = request.GET.get('category', '').strip().lower()
    if category_param in dict(Task.Category.choices):
        base_qs = base_qs.filter(category=category_param)

    # Priority filter
    priority_param = request.GET.get('priority', '').strip().lower()
    if priority_param in dict(Task.Priority.choices):
        base_qs = base_qs.filter(priority=priority_param)

    # Sorting
    sort_param = request.GET.get('sort', 'due_date').strip().lower()
    if sort_param == 'priority':
        base_qs = base_qs.order_by('completed', '-priority', 'due_date')
    elif sort_param == 'created_at':
        base_qs = base_qs.order_by('completed', '-created_at')
    elif sort_param == 'title':
        base_qs = base_qs.order_by('completed', 'title')
    else:  # default: due_date
        base_qs = base_qs.order_by('completed', 'due_date', '-priority')

    form = TaskForm()

    return render(request, 'myapp/task_list.html', {
        'tasks': base_qs,
        'total_count': total_count,
        'completed_count': completed_count,
        'pending_count': pending_count,
        'overdue_count': overdue_count,
        'progress_percentage': progress_percentage,
        'filter_param': filter_param,
        'category_param': category_param,
        'priority_param': priority_param,
        'sort_param': sort_param,
        'search_query': search_query,
        'categories': Task.Category.choices,
        'priorities': Task.Priority.choices,
        'today': today,
        'form': form,
        'is_gemini_configured': is_gemini_configured(),
    })


# ==============================================================================
# 3. Projects & Categories
# ==============================================================================

@ensure_csrf_cookie
def categories_view(request):
    """4. Projects & Categories: Organize tasks into projects or categories and view progress for each."""
    today = timezone.localdate()
    all_tasks = Task.objects.all()

    category_data = []
    category_meta = {
        'work': {'icon': '💼', 'desc': 'Professional projects, deliverables, team sprints, and meetings.'},
        'study': {'icon': '📚', 'desc': 'Tutorials, computer science concepts, exam review, and reading.'},
        'personal': {'icon': '🌱', 'desc': 'Health, habits, personal finance, home, and hobbies.'},
        'other': {'icon': '📌', 'desc': 'General logistics, quick notes, and miscellaneous items.'},
    }

    for cat_key, cat_label in Task.Category.choices:
        cat_tasks = all_tasks.filter(category=cat_key).order_by('completed', 'due_date')
        total = cat_tasks.count()
        completed = cat_tasks.filter(completed=True).count()
        pending = cat_tasks.filter(completed=False).count()
        high_priority = cat_tasks.filter(completed=False, priority=Task.Priority.HIGH).count()
        overdue = cat_tasks.filter(completed=False, due_date__lt=today).count()
        pct = int((completed / total) * 100) if total > 0 else 0

        meta = category_meta.get(cat_key, {'icon': '📁', 'desc': 'Project category'})

        category_data.append({
            'key': cat_key,
            'label': cat_label,
            'icon': meta['icon'],
            'desc': meta['desc'],
            'tasks': cat_tasks,
            'total': total,
            'completed': completed,
            'pending': pending,
            'high_priority': high_priority,
            'overdue': overdue,
            'progress_percentage': pct,
        })

    total_categories = len(Task.Category.choices)
    active_categories = sum(1 for c in category_data if c['total'] > 0)
    form = TaskForm()

    return render(request, 'myapp/categories.html', {
        'category_data': category_data,
        'total_categories': total_categories,
        'active_categories': active_categories,
        'total_tasks': all_tasks.count(),
        'form': form,
        'is_gemini_configured': is_gemini_configured(),
    })


# ==============================================================================
# 4. FAQs Page
# ==============================================================================

@ensure_csrf_cookie
def faq_list(request):
    """6. FAQs: Searchable, categorized software-development FAQs retrieved from SQLite."""
    base_qs = FAQ.objects.filter(is_published=True)

    # Search query
    query = request.GET.get('q', '').strip()
    if query:
        base_qs = base_qs.filter(
            Q(question__icontains=query) |
            Q(answer__icontains=query) |
            Q(keywords__icontains=query)
        )

    # Category filter
    selected_category = request.GET.get('category', '').strip()
    valid_categories = dict(FAQ.Category.choices)
    if selected_category in valid_categories:
        base_qs = base_qs.filter(category=selected_category)

    faqs = base_qs.order_by('category', 'question')

    # Display primary application categories in logical order
    primary_categories = [
        FAQ.Category.GETTING_STARTED,
        FAQ.Category.TASKS_CATEGORIES,
        FAQ.Category.AI_ASSISTANT,
        FAQ.Category.TROUBLESHOOTING_SUPPORT,
    ]
    active_in_db = set(FAQ.objects.filter(is_published=True).values_list('category', flat=True))
    categories_to_show = []
    for code, label in FAQ.Category.choices:
        if code in primary_categories:
            if (code, label) not in categories_to_show:
                categories_to_show.append((code, label))
        elif code in active_in_db:
            if (code, label) not in categories_to_show:
                categories_to_show.append((code, label))

    return render(request, 'myapp/faq_list.html', {
        'faqs': faqs,
        'categories': categories_to_show,
        'selected_category': selected_category,
        'search_query': query,
        'total_count': faqs.count(),
        'is_gemini_configured': is_gemini_configured(),
    })


# ==============================================================================
# 7. Error Code Guide Pages
# ==============================================================================

@ensure_csrf_cookie
def error_guide(request):
    """Searchable Error Code Guide with troubleshooting steps."""
    base_qs = ErrorCode.objects.all()

    query = request.GET.get('q', '').strip()
    if query:
        base_qs = base_qs.filter(
            Q(code__icontains=query) |
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(common_causes__icontains=query)
        )

    error_codes = base_qs.order_by('code')

    return render(request, 'myapp/error_guide.html', {
        'error_codes': error_codes,
        'search_query': query,
        'total_count': error_codes.count(),
        'is_gemini_configured': is_gemini_configured(),
    })


@ensure_csrf_cookie
def error_detail(request, code):
    """Detailed explanation, causes, troubleshooting, and suggested fixes for an error code."""
    error_obj = get_object_or_404(ErrorCode, code__iexact=code)
    related_faqs = FAQ.objects.filter(is_published=True).filter(
        Q(question__icontains=code) | Q(answer__icontains=code) | Q(keywords__icontains=code)
    )[:3]

    library_name = "django"
    if code in ['500', '503']:
        library_name = "gunicorn"
    elif code in ['400', '429']:
        library_name = "requests"

    package_docs = lookup_package_docs(library_name)

    return render(request, 'myapp/error_detail.html', {
        'error_obj': error_obj,
        'related_faqs': related_faqs,
        'package_docs': package_docs,
        'library_name': library_name,
        'is_gemini_configured': is_gemini_configured(),
    })


# ==============================================================================
# 8. Support Page (Ticket Submission & Status Lookup)
# ==============================================================================

@ensure_csrf_cookie
def support_view(request):
    """8. Support: Ticket submission and ticket confirmation, with appropriate privacy protections."""
    submitted_ref = request.GET.get('submitted', '').strip()
    submitted_ticket = None
    if submitted_ref:
        submitted_ticket = SupportTicket.objects.filter(reference=submitted_ref).first()

    # Ticket Lookup feature
    lookup_ref = request.GET.get('lookup_ref', '').strip()
    lookup_ticket = None
    lookup_searched = False
    if lookup_ref:
        lookup_searched = True
        lookup_ticket = SupportTicket.objects.filter(reference__iexact=lookup_ref).first()

    if request.method == 'POST':
        form = SupportTicketForm(request.POST)
        if form.is_valid():
            ticket = form.save()
            user_tickets = request.session.get('user_tickets', [])
            if ticket.reference not in user_tickets:
                user_tickets.append(ticket.reference)
            request.session['user_tickets'] = user_tickets
            request.session.modified = True
            messages.success(
                request,
                f"Support ticket created successfully! Your reference code is: {ticket.reference}."
            )
            return redirect(f"{request.path}?submitted={ticket.reference}")
        else:
            messages.error(request, "Please correct the errors in the ticket form below.")
    else:
        form = SupportTicketForm()

    return render(request, 'myapp/support.html', {
        'form': form,
        'submitted_ticket': submitted_ticket,
        'lookup_ticket': lookup_ticket,
        'lookup_ref': lookup_ref,
        'lookup_searched': lookup_searched,
        'user_tickets': request.session.get('user_tickets', []),
        'is_gemini_configured': is_gemini_configured(),
    })


# ==============================================================================
# 9. About Page
# ==============================================================================

@ensure_csrf_cookie
def about_view(request):
    """9. About: Explanation of the application, architecture, core features, and developer background."""
    # Handle POST for backward compatibility with tests posting to /about/
    if request.method == 'POST':
        form = SupportTicketForm(request.POST)
        if form.is_valid():
            ticket = form.save()
            user_tickets = request.session.get('user_tickets', [])
            if ticket.reference not in user_tickets:
                user_tickets.append(ticket.reference)
            request.session['user_tickets'] = user_tickets
            request.session.modified = True
            messages.success(
                request,
                f"Support ticket created successfully! Your reference code is: {ticket.reference}."
            )
            return redirect(f"{request.path}?submitted={ticket.reference}")
        else:
            messages.error(request, "Please correct the errors in the ticket form below.")
    else:
        form = SupportTicketForm()

    submitted_ref = request.GET.get('submitted', '').strip()
    submitted_ticket = None
    if submitted_ref:
        submitted_ticket = SupportTicket.objects.filter(reference=submitted_ref).first()

    total_tasks = Task.objects.count()
    total_faqs = FAQ.objects.filter(is_published=True).count()
    total_errors = ErrorCode.objects.count()

    return render(request, 'myapp/about.html', {
        'form': form,
        'submitted_ticket': submitted_ticket,
        'total_tasks': total_tasks,
        'total_faqs': total_faqs,
        'total_errors': total_errors,
        'is_gemini_configured': is_gemini_configured(),
    })

# Backward compatibility alias
about = about_view


# ==============================================================================
# AI Chat & Feedback Endpoints
# ==============================================================================

@require_POST
def chat_api(request):
    """Server-side AI Assistant endpoint.

    Workflow:
    1. Ground query in SQL FAQ and ErrorCode records.
    2. Pass database context to Gemini model.
    3. If unknown, offer support ticket escalation.
    4. Log conversation to MongoDB (with safe fail-soft fallback).
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'Invalid JSON body.'}, status=400)

    user_message = (data.get('message') or '').strip()
    if not user_message:
        return JsonResponse({'error': 'Message content cannot be empty.'}, status=400)

    conversation_id = (data.get('conversation_id') or 'anon_session').strip()[:64]
    history = data.get('history', [])

    # Basic rate-limiting per session (max 30 queries per minute in session)
    session_key = f'chat_count_{conversation_id}'
    current_time = datetime.now(dt_timezone.utc).timestamp()
    session_data = request.session.get(session_key, {'count': 0, 'first_time': current_time})

    if current_time - session_data['first_time'] < 60:
        if session_data['count'] > 30:
            return JsonResponse({
                'reply': "Rate limit reached: Please wait a moment before sending more messages.",
                'sources': [],
                'has_grounding': False,
                'suggest_ticket': True,
                'ticket_created': False,
            }, status=429)
        session_data['count'] += 1
    else:
        session_data = {'count': 1, 'first_time': current_time}
    request.session[session_key] = session_data

    # Generate assistant reply grounded in database
    ai_result = generate_support_assistant_response(user_message, conversation_history=history)

    # Persist interaction into MongoDB
    mongo_success, log_id = log_chat_interaction(
        conversation_id=conversation_id,
        user_message=user_message,
        assistant_response=ai_result['reply'],
        sources=ai_result['sources'],
        escalated=ai_result['escalated'],
        ticket_reference=ai_result.get('ticket_reference'),
    )

    if not mongo_success:
        logger.warning(f"[Chat API] MongoDB chat log was NOT saved for conversation {conversation_id[:16]}: {log_id}")

    return JsonResponse({
        'reply': ai_result['reply'],
        'sources': ai_result['sources'],
        'has_grounding': ai_result['has_grounding'],
        'suggest_ticket': ai_result['suggest_ticket'],
        'ticket_created': ai_result['ticket_created'],
        'ticket_reference': ai_result.get('ticket_reference'),
        'log_id': log_id if mongo_success else None,
        'mongo_saved': mongo_success,
    })


@require_POST
def chat_feedback_api(request):
    """Store thumbs up / down feedback and optional comments in MongoDB."""
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'Invalid JSON body.'}, status=400)

    conversation_id = (data.get('conversation_id') or '').strip()
    log_id = data.get('log_id')
    feedback_type = data.get('feedback_type', 'thumbs_up')
    comment = data.get('comment', '')

    if feedback_type not in ['thumbs_up', 'thumbs_down']:
        feedback_type = 'thumbs_up'

    success, msg = record_chat_feedback(
        conversation_id=conversation_id,
        log_id=log_id,
        feedback_type=feedback_type,
        comment=comment,
    )

    if not success:
        logger.warning(f"[Chat Feedback API] MongoDB feedback was NOT saved for conversation {conversation_id[:16]}: {msg}")

    return JsonResponse({
        'success': success,
        'message': msg,
    })


@require_POST
def ticket_create_api(request):
    """Direct API endpoint to submit a support ticket via chat widget or forms."""
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    subject = (data.get('subject') or 'Inquiry via AI Assistant').strip()[:255]
    description = (data.get('description') or '').strip()
    name = (data.get('name') or 'Anonymous Visitor').strip()[:100]
    email = (data.get('email') or '').strip()
    related_code = (data.get('related_error_code') or '').strip()[:50]

    if not description:
        return JsonResponse({'error': 'Description is required to create a ticket.'}, status=400)

    ticket = SupportTicket.objects.create(
        name=name,
        email=email,
        subject=subject,
        description=description,
        related_error_code=related_code,
        status=SupportTicket.Status.OPEN,
    )
    user_tickets = request.session.get('user_tickets', [])
    if ticket.reference not in user_tickets:
        user_tickets.append(ticket.reference)
    request.session['user_tickets'] = user_tickets
    request.session.modified = True

    return JsonResponse({
        'success': True,
        'reference': ticket.reference,
        'subject': ticket.subject,
        'message': f"Support ticket {ticket.reference} created successfully.",
    })


def ticket_update(request, reference):
    """Update an existing support ticket with authorization check."""
    ticket = get_object_or_404(SupportTicket, reference__iexact=reference)
    user_tickets = request.session.get('user_tickets', [])
    is_authorized = (ticket.reference in user_tickets) or (request.user.is_authenticated and request.user.is_staff)

    if not is_authorized:
        return render(request, 'myapp/403.html', {
            'error_title': 'Access Denied',
            'error_message': 'You do not have permission to modify this support ticket.',
        }, status=403)

    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        description = request.POST.get('description', '').strip()
        status_val = request.POST.get('status', '').strip()
        if subject:
            ticket.subject = subject[:255]
        if description:
            ticket.description = description
        if status_val in [s[0] for s in SupportTicket.Status.choices]:
            ticket.status = status_val
        ticket.save()
        messages.success(request, f"Ticket {ticket.reference} was updated successfully.")
        return redirect(f"/support/?lookup_ref={ticket.reference}")

    return render(request, 'myapp/support_ticket_edit.html', {
        'ticket': ticket,
        'status_choices': SupportTicket.Status.choices,
    })


def ticket_delete(request, reference):
    """Delete / cancel a support ticket with authorization check."""
    ticket = get_object_or_404(SupportTicket, reference__iexact=reference)
    user_tickets = request.session.get('user_tickets', [])
    is_authorized = (ticket.reference in user_tickets) or (request.user.is_authenticated and request.user.is_staff)

    if not is_authorized:
        return render(request, 'myapp/403.html', {
            'error_title': 'Access Denied',
            'error_message': 'You do not have permission to delete this support ticket.',
        }, status=403)

    if request.method == 'POST':
        ref = ticket.reference
        ticket.delete()
        if ref in user_tickets:
            user_tickets.remove(ref)
            request.session['user_tickets'] = user_tickets
            request.session.modified = True
        messages.success(request, f"Ticket {ref} has been removed.")
        return redirect('support')

    return redirect(f"/support/?lookup_ref={ticket.reference}")


@require_GET
def faq_api(request):
    """Machine-readable and AJAX API returning verified FAQ records from the SQL database."""
    base_qs = FAQ.objects.filter(is_published=True)

    category = request.GET.get('category', '').strip()
    if category:
        base_qs = base_qs.filter(category=category)

    query = request.GET.get('q', '').strip()
    if query:
        base_qs = base_qs.filter(
            Q(question__icontains=query) |
            Q(answer__icontains=query) |
            Q(keywords__icontains=query)
        )

    faq_records = []
    for f in base_qs:
        faq_records.append({
            'id': f.id,
            'question': f.question,
            'answer': f.answer,
            'category': f.category,
            'keywords': f.keywords,
        })

    categories_data = [
        {'code': code, 'label': label}
        for code, label in FAQ.Category.choices
    ]

    return JsonResponse({
        'status': 'success',
        'faqs': faq_records,
        'total_count': len(faq_records),
        'categories': categories_data,
        'selected_category': category,
        'search_query': query,
    })


@require_GET
def package_lookup_api(request):
    """AJAX endpoint for third-party PyPI library documentation lookups."""
    pkg_name = request.GET.get('name', '').strip()
    data = lookup_package_docs(pkg_name)
    return JsonResponse(data)


# ==============================================================================
# Health Check Endpoint
# ==============================================================================

@require_GET
def health_check(request):
    """Machine-readable health endpoint (/health/). Checks SQL and MongoDB readiness."""
    # 1. SQL Database Check
    sql_ok = False
    sql_type = "sqlite3"
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            row = cursor.fetchone()
            if row and row[0] == 1:
                sql_ok = True
                sql_type = connection.vendor
    except Exception as exc:
        logger.error(f"SQL Health check failed: {type(exc).__name__}")
        sql_ok = False

    # 2. MongoDB Check
    mongo_diag = check_mongo_connection()

    # 3. Gemini Config Check
    gemini_ready = is_gemini_configured()

    status_str = "healthy" if sql_ok else "degraded"
    http_status = 200 if sql_ok else 503

    return JsonResponse({
        'status': status_str,
        'timestamp': datetime.now(dt_timezone.utc).isoformat(),
        'services': {
            'sql_database': {
                'status': 'connected' if sql_ok else 'disconnected',
                'engine': sql_type,
            },
            'mongodb': mongo_diag,
            'gemini_ai': {
                'configured': gemini_ready,
                'model': DEFAULT_MODEL,
            },
        },
        'environment': {
            'debug': settings.DEBUG,
            'version': '1.0.0',
        }
    }, status=http_status)


# ==============================================================================
# Custom Error Handlers
# ==============================================================================

def custom_bad_request_view(request, exception=None):
    """Custom 400 Bad Request error view."""
    return render(request, 'myapp/400.html', status=400)


def custom_permission_denied_view(request, exception=None):
    """Custom 403 Forbidden error view."""
    return render(request, 'myapp/403.html', status=403)


def custom_page_not_found_view(request, exception=None):
    """Custom 404 Not Found error view."""
    return render(request, '404.html', status=404)


def custom_server_error_view(request):
    """Custom 500 Internal Server Error view."""
    try:
        return render(request, '500.html', status=500)
    except Exception as exc:
        logger.error(f"Error rendering custom 500 template: {exc}", exc_info=True)
        from django.http import HttpResponseServerError
        return HttpResponseServerError(
            "<!DOCTYPE html><html><head><title>500 - Server Error</title></head><body><h1>Something went wrong</h1><p>The server encountered an unexpected error.</p></body></html>",
            content_type="text/html"
        )


# ==============================================================================
# Preserved TaskFlow Views (Backward Compatibility)
# ==============================================================================

def task_list(request):
    """Preserved TaskFlow task dashboard."""
    today = timezone.localdate()
    base_qs = Task.objects.all()
    total_count = base_qs.count()
    completed_count = base_qs.filter(completed=True).count()
    pending_count = base_qs.filter(completed=False).count()
    overdue_count = base_qs.filter(completed=False, due_date__lt=today).count()
    progress_percentage = int((completed_count / total_count) * 100) if total_count > 0 else 0

    filter_param = request.GET.get('filter', 'all').strip().lower()
    tasks = base_qs
    if filter_param == 'pending':
        tasks = tasks.filter(completed=False)
    elif filter_param == 'completed':
        tasks = tasks.filter(completed=True)
    elif filter_param == 'overdue':
        tasks = tasks.filter(completed=False, due_date__lt=today)

    category_param = request.GET.get('category', '').strip().lower()
    if category_param in dict(Task.Category.choices):
        tasks = tasks.filter(category=category_param)

    search_query = request.GET.get('q', '').strip()
    if search_query:
        tasks = tasks.filter(title__icontains=search_query)

    tasks = tasks.order_by('completed', '-created_at')

    return render(request, 'myapp/task_list.html', {
        'tasks': tasks,
        'total_count': total_count,
        'completed_count': completed_count,
        'pending_count': pending_count,
        'overdue_count': overdue_count,
        'progress_percentage': progress_percentage,
        'filter_param': filter_param,
        'category_param': category_param,
        'search_query': search_query,
        'categories': Task.Category.choices,
        'priorities': Task.Priority.choices,
        'is_gemini_configured': is_gemini_configured(),
        'today': today,
    })


def add_task(request):
    """Add a new task via POST request."""
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save()
            messages.success(request, f'Task "{task.title}" added.')
        else:
            title = request.POST.get('title', '').strip()
            if title:
                Task.objects.create(title=title[:255])
                messages.success(request, f'Task "{title}" added.')
            else:
                messages.error(request, 'Task title cannot be empty.')
    return redirect('task_list')


def edit_task(request, task_id):
    """Edit an existing task."""
    task = get_object_or_404(Task, id=task_id)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, f'Task "{task.title}" updated.')
            return redirect('task_list')
        else:
            messages.error(request, 'Please correct the errors in the task form.')
    else:
        form = TaskForm(instance=task)
    return render(request, 'myapp/task_edit.html', {'form': form, 'task': task})


def toggle_task(request, task_id):
    """Toggle a task between complete and incomplete."""
    if request.method == 'POST':
        task = get_object_or_404(Task, id=task_id)
        task.completed = not task.completed
        task.save()
    return redirect('task_list')


def delete_task(request, task_id):
    """Delete a task."""
    if request.method == 'POST':
        task = get_object_or_404(Task, id=task_id)
        task.delete()
        messages.success(request, "Task deleted.")
    return redirect('task_list')


def task_breakdown(request):
    """AI Task Breakdown view."""
    return render(request, 'myapp/task_breakdown.html', {
        'is_gemini_configured': is_gemini_configured(),
        'suggestions': [],
        'goal': '',
        'deadline': '',
        'available_time': '',
        'priorities': Task.Priority.choices,
    })


def daily_planner(request):
    """AI Daily Planner view."""
    pending_tasks = Task.objects.filter(completed=False)
    return render(request, 'myapp/daily_planner.html', {
        'is_gemini_configured': is_gemini_configured(),
        'pending_tasks': pending_tasks,
        'plan_result': None,
        'available_time_input': '',
    })
