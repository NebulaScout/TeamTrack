from rest_framework import viewsets
from django.contrib.auth.models import User
from rest_framework_simplejwt.authentication import JWTAuthentication

from .serializers import RegistrationSerializer, UserSerializer
from accounts.models import RegisterModel
from .permissions import UserPermissions

class RegisterViewSet(viewsets.ModelViewSet):
    queryset = RegisterModel.objects.all()
    serializer_class = RegistrationSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [UserPermissions]

class ProfileViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [UserPermissions]