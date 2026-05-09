"""Models - updated for Django 5.

Security-relevant changes:
  * `reset_token` is now `null=True, default=None` - report.txt 2.4 (CWE-259)
  * `ForeignKey` / `OneToOneField` require explicit `on_delete` in Django 5
  * `NullBooleanField` removed - replaced with `BooleanField(null=True)`
"""
import datetime

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


def _due_in_a_week():
    return timezone.now() + datetime.timedelta(weeks=1)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.CharField(max_length=3000, default="")
    # SECURITY: use NULL (not "") for absent reset tokens (report 2.4)
    reset_token = models.CharField(
        max_length=100, null=True, blank=True, default=None,
    )
    reset_token_expiration = models.DateTimeField(default=timezone.now)


class Project(models.Model):
    title = models.CharField(max_length=50, default='Default')
    text = models.CharField(max_length=500)
    start_date = models.DateTimeField('date started')
    due_date = models.DateTimeField('date due', default=_due_in_a_week)
    users_assigned = models.ManyToManyField(User)
    priority = models.IntegerField(default=1)

    def __str__(self):
        return self.title

    def was_created_recently(self):
        return self.start_date >= timezone.now() - datetime.timedelta(days=1)

    def is_overdue(self):
        return self.due_date <= timezone.now()

    def percent_complete(self):
        tasks = self.task_set.all()
        if not tasks:
            return 0
        done = sum(1 for t in tasks if t.completed)
        return round(done / tasks.count() * 100)

    def percent_bucket(self):
        # SECURITY: discrete bucket lets templates pick a CSS class
        # instead of using an inline style="" (avoids style-src 'unsafe-inline').
        return int(round(self.percent_complete() / 10.0)) * 10


class Task(models.Model):
    project = models.ForeignKey(Project, default=1, on_delete=models.CASCADE)
    text = models.CharField(max_length=200)
    title = models.CharField(max_length=200, default="N/A")
    start_date = models.DateTimeField('date created')
    due_date = models.DateTimeField('date due', default=_due_in_a_week)
    completed = models.BooleanField(null=True, default=False)
    users_assigned = models.ManyToManyField(User)

    def __str__(self):
        return self.text

    def was_created_recently(self):
        return self.start_date >= timezone.now() - datetime.timedelta(days=1)

    def is_overdue(self):
        return self.due_date <= timezone.now()

    def percent_complete(self):
        return 100 if self.completed else 0


class Notes(models.Model):
    task = models.ForeignKey(Task, default=1, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, default="N/A")
    text = models.CharField(max_length=200)
    image = models.CharField(max_length=200, blank=True, default="")
    user = models.CharField(max_length=200, default='ancestor')

    def __str__(self):
        return self.text


class File(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=300, default="")
    path = models.CharField(max_length=3000, default="")

    def __str__(self):
        return self.name
