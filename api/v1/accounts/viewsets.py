from rest_framework import viewsets, status
from django.contrib.auth.models import User
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import RegistrationSerializer, UserSerializer
from accounts.models import RegisterModel
from utils.permissions import UserPermissions
from core.services.group_assignment import set_user_role

class RegisterViewSet(viewsets.ModelViewSet):
    queryset = RegisterModel.objects.all()
    serializer_class = RegistrationSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [UserPermissions]

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get the current authenticated user's profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def assign_role(self, request, pk=None):
        """Assing a role to a user"""
        role = request.data.get("role")

        if not role:
            Response({"error": "Role is required"},
                     status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=pk)
            set_user_role(user, role)
            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "User not found"},
                            status=status.HTTP_404_NOT_FOUND)
        except RuntimeError as e:
            return Response({"error": str(e)},
                            status=status.HTTP_400_BAD_REQUEST)

class ProfileViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [UserPermissions]

