from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.models import User

from core.services.roles import ROLE_PERMISSIONS


class ProjectsModel(models.Model):
    project_name = models.CharField(max_length=100, blank=False, unique=True)
    description = models.TextField()
    start_date = models.DateField(default=timezone.now, blank=False)
    end_date = models.DateField() # TODO: add validation where start_date > end_date
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    created_at = models.DateField(auto_now_add=True)
    # updated_at = models.DateTimeField()

    class Meta:
        permissions = [
            ("assign_project", "Can assign a project to users"),
        ]

class ProjectMembers(models.Model):
    ROLE_CHOICES = [(role, role) for role in ROLE_PERMISSIONS.keys()] # Fetch the defined permissions

    project = models.ForeignKey(ProjectsModel, on_delete=models.CASCADE, related_name='members') # record reprsents one user has one role in the project
    project_member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_memberships') # a user can be a member of multiple projects
    role_in_project = models.CharField(max_length=50, choices=ROLE_CHOICES, default='Guest')

    class Meta:
        unique_together = ('project', 'project_member') # A user can only be added once per project