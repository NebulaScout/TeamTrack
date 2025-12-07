from django.db import models
from django.contrib.auth.models import User
from django_enum import EnumField

class RegisterModel(models.Model):
    class RoleEnum(models.TextChoices):
       ADMIN =  'ADMIN', 'Admin'
       PROJECT_MANAGER = 'PM', 'Project Manager'
       DEVELOPER = 'DEV', 'Developer'
       STAKEHOLDER = 'SH', 'Stakeholder'

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=5, choices=RoleEnum.choices, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


