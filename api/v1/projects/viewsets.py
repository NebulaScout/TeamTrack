from rest_framework import viewsets, status, permissions
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db.models import Q

from projects.models import ProjectsModel
from .serializers import ProjectsSerializer, ExtendedUserSerializer, ProjectMemberSerializer, ExtendedProjectsSerializer
from core.services.permissions import ProjectPermissions
from core.services.project_service import ProjectService

class ProjectsViewSet(viewsets.ModelViewSet):
    # queryset = ProjectsModel.objects.all()
    serializer_class = ExtendedProjectsSerializer
    permission_classes = [ProjectPermissions]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self): # type: ignore
        user = self.request.user 

        return (
            ProjectsModel.objects
            .filter( # Return if:
                Q(created_by=user) | # project was created by the user or
                Q(members__project_member=user) # user has been assigned to the project
            )
            .distinct() # remove duplicates
            .prefetch_related('members', 'members__project_member') # retrive related records for better performance
            .select_related('created_by')
        )
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        project = ProjectService.create_project(
           user = request.user,
           data = serializer.validated_data
        )

        output_serializer = self.get_serializer(project)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path="members")
    def add_members(self, request, pk=None):
        project = self.get_object()

        serializer = ProjectMemberSerializer(
            data = request.data,
            context = {"request": request}
        )

        serializer.is_valid(raise_exception=True)
        serializer.save(project=project)

        return Response(serializer.data, status = status.HTTP_201_CREATED)
        

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = ExtendedUserSerializer