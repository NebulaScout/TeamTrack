from rest_framework import viewsets
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import User

from projects.models import ProjectsModel
from .serializers import ProjectsSerializer, ExtendedUserSerializer
from utils.permissions import ProjectPermissions

class ProjectsViewSet(viewsets.ModelViewSet):
    queryset = ProjectsModel.objects.all()
    serializer_class = ProjectsSerializer
    # permission_classes = [ProjectPermissions]
    # authentication_classes = [JWTAuthentication]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = ExtendedUserSerializer