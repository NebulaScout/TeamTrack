from django.db import models
from django.contrib.auth.models import User
from django_enum import EnumField

from projects.models import ProjectsModel
from core.services.enums import PriorityEnum, StatusEnum

class TaskModel(models.Model):
    project = models.ForeignKey(ProjectsModel, on_delete=models.CASCADE, related_name='project_tasks', blank=False)
    title = models.CharField(max_length=100)
    description = models.TextField()
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='assigned_tasks', null=True)
    status = EnumField(StatusEnum, null=True, blank=True)
    priority = EnumField(PriorityEnum, null=True, blank=True)
    due_date = models.DateField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='created_tasks', null=True)
    created_at = models.DateTimeField(auto_now_add=True)