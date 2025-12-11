from rest_framework import serializers
from django.contrib.auth.models import User

from .models import RegisterModel

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email','password', 'confirm_password']

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords do not match!!")
        return attrs
    
    def create(self, validated_data):
        # Remove password entries from serializer
        password = validated_data.pop('password')
        validated_data.pop('confirm_password')

        user = User(**validated_data)
        user.set_password(password) # hash password
        user.save()
        return user
    
    
class RegistrationSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = RegisterModel
        fields = '__all__'

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        # Create user first
        user = UserSerializer().create(user_data) 
        # then assign it to the register model so as to include the user_id
        registration = RegisterModel.objects.create(user=user, **validated_data)

        return registration