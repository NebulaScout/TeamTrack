from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class ProjectsModel(models.Model):
    project_name = models.CharField(max_length=100, blank=False, unique=True)
    description = models.TextField()
    start_date = models.DateTimeField(default=timezone.now, blank=False)
    end_date = models.DateTimeField() # TODO: add validation where start_date > end_date
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    created_at = models.DateTimeField(auto_now_add=True)
    # updated_at = models.DateTimeField()
