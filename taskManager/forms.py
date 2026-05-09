"""Forms - updated for Django 5 (no security issues flagged in report)."""
from django import forms
from django.contrib.auth.models import User

from taskManager.models import Project, Task


def get_my_choices_users():
    return [(i, u) for i, u in enumerate(User.objects.order_by('date_joined'), 1)]


def get_my_choices_tasks(current_proj):
    tasks = [t for t in Task.objects.all() if t.project == current_proj]
    return [(i, t) for i, t in enumerate(tasks, 1)]


def get_my_choices_projects():
    return [(i, p) for i, p in enumerate(Project.objects.all(), 1)]


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        exclude = [
            'groups', 'user_permissions',
            'last_login', 'date_joined', 'is_active',
        ]


class ProjectFileForm(forms.Form):
    name = forms.CharField(max_length=300)
    file = forms.FileField()


class ProfileForm(forms.Form):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.CharField(max_length=300, required=False)
    picture = forms.FileField(required=False)
