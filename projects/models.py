from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


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
