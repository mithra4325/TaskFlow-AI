from django.contrib import admin
from .models import Task, FAQ, ErrorCode, SupportTicket


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'priority',
        'category',
        'due_date',
        'estimated_duration',
        'completed',
        'created_at',
    )
    list_filter = ('completed', 'priority', 'category', 'due_date', 'created_at')
    search_fields = ('title', 'description')
    list_editable = ('completed', 'priority')


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'is_published', 'updated_at')
    list_filter = ('category', 'is_published')
    search_fields = ('question', 'answer', 'keywords')
    list_editable = ('is_published',)


@admin.register(ErrorCode)
class ErrorCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'status_code', 'updated_at')
    search_fields = ('code', 'title', 'description', 'common_causes')


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('reference', 'subject', 'status', 'name', 'email', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('reference', 'subject', 'description', 'email', 'name')
    readonly_fields = ('reference', 'created_at', 'updated_at')
