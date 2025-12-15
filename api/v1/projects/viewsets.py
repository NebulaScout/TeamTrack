from rest_framework import viewsets, status
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import User
from rest_framework.response import Response

from projects.models import ProjectsModel
from .serializers import ProjectsSerializer, ExtendedUserSerializer
from utils.permissions import ProjectPermissions
from services.project_service import ProjectService

class ProjectsViewSet(viewsets.ModelViewSet):
    queryset = ProjectsModel.objects.all()
    serializer_class = ProjectsSerializer
    permission_classes = [ProjectPermissions]
    authentication_classes = [JWTAuthentication]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        project = ProjectService.create_project(
           user = request.user ,
           data = serializer.validated_data
        )

        output_serializer = self.get_serializer(project)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
        return super().create(request, *args, **kwargs)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = ExtendedUserSerializer