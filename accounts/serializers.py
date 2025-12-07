from rest_framework import serializers

from .models import RegisterModel

class RegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegisterModel
        fields = ['user', 'role', 'created_at']
