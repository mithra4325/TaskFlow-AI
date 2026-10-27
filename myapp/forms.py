from django import forms
from .models import Task, SupportTicket


class TaskForm(forms.ModelForm):
    completed = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'id': 'task-completed-input'}))

    class Meta:
        model = Task
        fields = ['title', 'description', 'priority', 'category', 'due_date', 'estimated_duration', 'completed']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'What needs to be done?',
                'maxlength': '255',
                'required': True,
                'id': 'task-title-input',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Optional details or notes...',
                'rows': 3,
                'id': 'task-description-input',
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select',
                'id': 'task-priority-input',
            }),
            'category': forms.Select(attrs={
                'class': 'form-select',
                'id': 'task-category-input',
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'id': 'task-duedate-input',
            }),
            'estimated_duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '30',
                'min': '5',
                'max': '480',
                'id': 'task-duration-input',
            }),
        }

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if not title:
            raise forms.ValidationError("Task title cannot be empty.")
        return title


class TaskBreakdownForm(forms.Form):
    goal = forms.CharField(
        max_length=500,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Prepare for my Django practical exam, launch my portfolio site...',
            'id': 'ai-goal-input',
            'required': True,
        }),
        label="Goal or Project",
    )
    deadline = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., This Friday, in 3 days, or YYYY-MM-DD',
            'id': 'ai-deadline-input',
        }),
        label="Target Deadline (Optional)",
    )
    available_time = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., 2 hours per day, 6 hours total',
            'id': 'ai-available-time-input',
        }),
        label="Available Study/Work Time (Optional)",
    )


class DailyPlannerForm(forms.Form):
    available_time_input = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., 4 hours or 180 minutes',
            'id': 'ai-planner-time-input',
        }),
        label="Available Time Today",
        help_text="Specify time in hours (e.g. '4h') or minutes (e.g. '120m'). Leave empty for full day.",
    )

    def get_available_minutes(self):
        val = self.cleaned_data.get('available_time_input', '').strip().lower()
        if not val:
            return None
        try:
            if 'h' in val:
                num = float(val.replace('hours', '').replace('hour', '').replace('h', '').strip())
                return int(num * 60)
            elif 'm' in val:
                num = float(val.replace('minutes', '').replace('minute', '').replace('mins', '').replace('min', '').replace('m', '').strip())
                return int(num)
            else:
                num = float(val)
                if num <= 16:
                    return int(num * 60)
                return int(num)
        except (ValueError, TypeError):
            return None


class SupportTicketForm(forms.ModelForm):
    """User-facing support ticket form with basic spam honeypot validation."""
    honey_field = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = SupportTicket
        fields = ['name', 'email', 'subject', 'description', 'related_error_code']
        error_messages = {
            'subject': {
                'required': 'Subject cannot be empty.',
            },
            'description': {
                'required': 'Description cannot be empty.',
            },
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Name or Alias (Optional)',
                'id': 'ticket-name-input',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your.email@example.com (Optional)',
                'id': 'ticket-email-input',
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief summary of the issue (e.g. 500 error on POST request)...',
                'required': True,
                'maxlength': '255',
                'id': 'ticket-subject-input',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Explain what occurred, error message, steps to reproduce, or question...',
                'rows': 4,
                'required': True,
                'id': 'ticket-desc-input',
            }),
            'related_error_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 404, 500, or DEV001 (Optional)',
                'id': 'ticket-error-input',
            }),
        }

    def clean_subject(self):
        subj = self.cleaned_data.get('subject', '').strip()
        if not subj:
            raise forms.ValidationError("Subject cannot be empty.")
        return subj[:255]

    def clean_description(self):
        desc = self.cleaned_data.get('description', '').strip()
        if not desc:
            raise forms.ValidationError("Description cannot be empty.")
        return desc

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('honey_field'):
            raise forms.ValidationError("Spam request rejected.")
        return cleaned_data
