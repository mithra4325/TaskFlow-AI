from django.urls import path
from . import views

urlpatterns = [
    # 1. Dashboard (Primary Entry & Navigation)
    path('', views.dashboard, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # 2. My Tasks (Full Task Management CRUD)
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/add/', views.add_task, name='add_task'),
    path('tasks/edit/<int:task_id>/', views.edit_task, name='edit_task'),
    path('tasks/toggle/<int:task_id>/', views.toggle_task, name='toggle_task'),
    path('tasks/delete/<int:task_id>/', views.delete_task, name='delete_task'),

    # 3. Projects & Categories
    path('categories/', views.categories_view, name='categories'),

    # 6. Developer FAQs
    path('faqs/', views.faq_list, name='faq_list'),

    # 7. Error Code Guide
    path('errors/', views.error_guide, name='error_guide'),
    path('errors/<str:code>/', views.error_detail, name='error_detail'),

    # 8. Support (Ticket submission, status lookup, privacy protection, and CRUD)
    path('support/', views.support_view, name='support'),
    path('support/ticket/<str:reference>/update/', views.ticket_update, name='ticket_update'),
    path('support/ticket/<str:reference>/delete/', views.ticket_delete, name='ticket_delete'),

    # 9. About Application
    path('about/', views.about_view, name='about'),

    # AI Chat, Feedback, FAQs API, Third-Party Docs Lookup, and Health
    path('api/faqs/', views.faq_api, name='faq_api'),
    path('api/chat/', views.chat_api, name='chat_api'),
    path('api/chat/feedback/', views.chat_feedback_api, name='chat_feedback_api'),
    path('api/tickets/create/', views.ticket_create_api, name='ticket_create_api'),
    path('api/package-lookup/', views.package_lookup_api, name='package_lookup_api'),
    path('health/', views.health_check, name='health_check'),

    # AI Productivity Assistants (Breakdown & Daily Planner)
    path('tasks/breakdown/', views.task_breakdown, name='task_breakdown'),
    path('tasks/planner/', views.daily_planner, name='daily_planner'),
]

