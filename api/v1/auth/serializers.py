from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class TokenDataSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField()

class LoginResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    token_data = TokenDataSerializer(source='data')