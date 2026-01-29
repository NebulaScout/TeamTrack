from rest_framework import serializers
from django.contrib.auth.models import User

from accounts.models import RegisterModel, UserProfile
from core.services.registration_service import register_user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    role = serializers.SerializerMethodField()
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id' ,'username', 'first_name', 'last_name', 'email','password', 'confirm_password',
                  'role', 'profile']
        
    def get_role(self, obj):
        """Return a users primary role"""
        group = obj.groups.first()
        return group.name if group else None

 
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
    
