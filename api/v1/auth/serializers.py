from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed

class TokenDataSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField()

class LoginResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    token_data = TokenDataSerializer(source='data')

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        try:
            return super().validate(attrs)
        except AuthenticationFailed:
            raise AuthenticationFailed("Invalid email or password")
