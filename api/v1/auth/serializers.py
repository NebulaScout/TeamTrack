from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


User = get_user_model()


class TokenDataSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField()


class LoginResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    token_data = TokenDataSerializer(source="data")


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    email = serializers.EmailField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[self.username_field].required = False

    def validate(self, attrs):
        username = attrs.get(self.username_field)
        email = attrs.get("email")

        if not username and not email:
            raise serializers.ValidationError(
                {"username": ["Username or email is required."]}
            )

        if email and not username:
            try:
                user = User.objects.get(email__iexact=email)
                attrs[self.username_field] = user.get_username()
            except User.DoesNotExist:
                raise AuthenticationFailed("Email does not exist")

        try:
            return super().validate(attrs)
        except AuthenticationFailed:
            raise AuthenticationFailed("Invalid username/email or password")
