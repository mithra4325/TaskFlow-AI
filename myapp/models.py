import uuid
from django.db import models
from django.utils import timezone


class Task(models.Model):
    """Preserved core Task model from previous iteration."""
    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'

    class Category(models.TextChoices):
        WORK = 'work', 'Work'
        STUDY = 'study', 'Study'
        PERSONAL = 'personal', 'Personal'
        OTHER = 'other', 'Other'

    title = models.CharField(max_length=255)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, default='')
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.OTHER,
    )
    due_date = models.DateField(null=True, blank=True)
    estimated_duration = models.PositiveIntegerField(
        null=True,
        blank=True,
        default=30,
        help_text="Estimated duration in minutes",
    )

    class Meta:
        ordering = ['completed', '-created_at']

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        if self.due_date and not self.completed:
            return self.due_date < timezone.localdate()
        return False


class FAQ(models.Model):
    """Frequently Asked Questions for TaskFlow AI task management and support."""
    class Category(models.TextChoices):
        GETTING_STARTED = 'Getting Started', 'Getting Started'
        TASKS_CATEGORIES = 'Tasks & Categories', 'Tasks & Categories'
        AI_ASSISTANT = 'AI Assistant', 'AI Assistant'
        TROUBLESHOOTING_SUPPORT = 'Troubleshooting & Support', 'Troubleshooting & Support'

        # Legacy choices for backward compatibility
        DJANGO = 'Django', 'Django Framework'
        PYTHON = 'Python', 'Python Programming'
        WEB_HTTP = 'Web & HTTP', 'Web & HTTP Protocols'
        SECURITY = 'Security', 'Security & Secrets'
        DATABASE = 'Database', 'Databases & Migrations'
        GENERAL = 'General', 'General Development'

    question = models.CharField(max_length=255, db_index=True)
    answer = models.TextField(help_text="Clear, beginner-friendly explanation and solution.")
    category = models.CharField(
        max_length=50,
        choices=Category.choices,
        default=Category.GENERAL,
        db_index=True,
    )
    keywords = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="Comma-separated keywords for search and AI grounding.",
    )
    is_published = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'question']
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"
        indexes = [
            models.Index(fields=['category', 'is_published']),
            models.Index(fields=['question']),
        ]

    def __str__(self):
        return f"[{self.category}] {self.question}"


class ErrorCode(models.Model):
    """Developer Error Code Guide for HTTP status codes and custom site exceptions."""
    code = models.CharField(max_length=20, unique=True, db_index=True)
    title = models.CharField(max_length=150)
    status_code = models.IntegerField(null=True, blank=True, help_text="HTTP status code if applicable.")
    description = models.TextField(help_text="Overview of what this error code signifies.")
    common_causes = models.TextField(help_text="Bulleted or paragraph explanation of common causes.")
    troubleshooting_steps = models.TextField(help_text="Step-by-step diagnostic actions.")
    suggested_fixes = models.TextField(help_text="Code snippets or configuration corrections.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['code']
        verbose_name = "Error Code"
        verbose_name_plural = "Error Codes"

    def __str__(self):
        return f"{self.code} — {self.title}"


class SupportTicket(models.Model):
    """Support Ticket created directly by visitors or escalated from AI assistant."""
    class Status(models.TextChoices):
        OPEN = 'Open', 'Open'
        IN_PROGRESS = 'In Progress', 'In Progress'
        RESOLVED = 'Resolved', 'Resolved'

    reference = models.CharField(max_length=32, unique=True, db_index=True)
    name = models.CharField(max_length=100, blank=True, default="Anonymous Visitor")
    email = models.EmailField(blank=True, default="")
    subject = models.CharField(max_length=255)
    description = models.TextField()
    related_error_code = models.CharField(max_length=50, blank=True, default="")
    related_faq = models.ForeignKey(
        FAQ,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='tickets',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Support Ticket"
        verbose_name_plural = "Support Tickets"

    @classmethod
    def generate_reference(cls):
        """Generate a clean, professional unique ticket reference."""
        return f"TICK-{uuid.uuid4().hex[:8].upper()}"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self.generate_reference()
            while SupportTicket.objects.filter(reference=self.reference).exists():
                self.reference = self.generate_reference()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.reference}] {self.subject} ({self.status})"
