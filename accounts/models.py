from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import Group

class RegisterModel(models.Model):

   #TODO: Make email field unique (check proper migration techniques to prevent data loss)
    user = models.OneToOneField(User, on_delete=models.CASCADE) 
    created_at = models.DateTimeField(auto_now_add=True)

    
