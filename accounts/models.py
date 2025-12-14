from django.db import models
from django.contrib.auth.models import User
from django_enum import EnumField

class RegisterModel(models.Model):
   #  class RoleEnum(models.TextChoices):
   #     ADMIN =  'ADMIN', 'Admin'
   #     PROJECT_MANAGER = 'PM', 'Project Manager'
   #     DEVELOPER = 'DEV', 'Developer'
   #     GUEST = 'GT', 'Guest'

   #TODO: Make email field unique (check proper migration techniques to prevent data loss)
    user = models.OneToOneField(User, on_delete=models.CASCADE) 
    created_at = models.DateTimeField(auto_now_add=True)
    
