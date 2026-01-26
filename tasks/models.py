from django.db import models
from django.contrib.auth.models import User
from django_enum import EnumField
from django.utils import timezone

from projects.models import ProjectsModel, ProjectMembers
from core.services.enums import PriorityEnum, StatusEnum, TaskFieldEnum

class Status(models.Model):
    name = EnumField(StatusEnum, null=True, blank=True)
class TaskModel(models.Model):
    project = models.ForeignKey(ProjectsModel, on_delete=models.CASCADE, related_name='project_tasks', blank=False)
    title = models.CharField(max_length=100)
    description = models.TextField()
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='assigned_tasks', null=True) # TODO: Change this to project member
    status = models.ForeignKey(Status, on_delete=models.SET_NULL, null=True, related_name='task_status')
    priority = EnumField(PriorityEnum, null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='created_tasks', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class CommentModel(models.Model):
    task = models.ForeignKey(TaskModel, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='task_comments')
    content = models.TextField(blank=False)
    created_at = models.DateTimeField(auto_now_add=True)

class TaskHistoryModel(models.Model):
    task = models.ForeignKey(TaskModel, on_delete=models.SET_NULL, null=True, related_name='history')
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='task_changes')
    field_changed = EnumField(TaskFieldEnum)
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)


class TaskAssignment(models.Model):
    task = models.ForeignKey(TaskModel, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)