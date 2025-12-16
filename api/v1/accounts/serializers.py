from rest_framework import serializers
from django.contrib.auth.models import User

from accounts.models import RegisterModel
from core.services.registration_service import register_user

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email','password', 'confirm_password']

    
    
class RegistrationSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = RegisterModel
        fields = '__all__'

    def create(self, validated_data):
        user_data = validated_data.pop('user')
       
        return register_user(
            first_name = user_data["first_name"],
            last_name = user_data["last_name"],
            username = user_data["username"],
            email = user_data["email"],
            password = user_data["password"],
        )