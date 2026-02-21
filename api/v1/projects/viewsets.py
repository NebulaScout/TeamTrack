from rest_framework import viewsets, status
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from drf_spectacular.utils import extend_schema

from projects.models import ProjectsModel
from .serializers import (
    ExtendedUserSerializer,
    ProjectMemberSerializer,
    ExtendedProjectsSerializer,
    TaskSerializer,
    ProjectsSerializer)
from core.services.permissions import ProjectPermissions
from core.services.project_service import ProjectService
from core.services.task_service import TaskService
from core.services.permissions import ROLE_PERMISSIONS
from api.v1.common.responses import ResponseMixin

from tasks.models import TaskModel

class ProjectsViewSet(ResponseMixin, viewsets.ModelViewSet):
    permission_classes = [ProjectPermissions]
    authentication_classes = [JWTAuthentication]
    serializer_class = ProjectsSerializer

    def get_queryset(self): # type: ignore
        user = self.request.user 
        user_groups = user.groups.values_list('name', flat=True)

        # Check if user has permission to view all projects
        can_view_all = any(
            'view_projectsmodel' in ROLE_PERMISSIONS.get(group, [])
            for group in user_groups
        )

        # If a user has view_projectsmodel permission, they can view all created projects
        if can_view_all:
            projects = ProjectsModel.objects.all().distinct().prefetch_related('members', 'members__project_member').select_related('created_by')
            return self._success(data=projects, message="Projects retrieved successfully")

        return self._success(
            data = ProjectsModel.objects
                .filter( # Return if:
                    Q(created_by=user) | # project was created by the user or
                    Q(members__project_member=user) # user has been assigned to the project
                )
                .distinct() # remove duplicates
                .prefetch_related('members', 'members__project_member') # retrive related records for better performance
                .select_related('created_by'),
            message="Projects retrieved successfully"
        )
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return self._error(
                "INVALID_INPUT",
                "Error creating project! Please confirm all fields have the necessary data.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        
        project = ProjectService.create_project(
           user = request.user,
           data = serializer.validated_data
        )

        output_serializer = self.get_serializer(project)
        return self._success(data=output_serializer.data, message="Project created successfully", status=status.HTTP_201_CREATED)
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
            request=TaskSerializer,
            responses={
                200: TaskSerializer(many=True),
                201: TaskSerializer()
            },
            methods=['GET', 'POST']
    )
    
    @action(detail=True, methods=['post', 'get'], url_path='tasks')
    def tasks(self, request, pk=None):
        """Handle tasks for a project"""

        # get project id from the url parameter
        project = self.get_object()

        if request.method == 'POST':
            # Create a new task
            serializer = TaskSerializer(data = request.data)
            # serializer.is_valid(raise_exception=True)

            if not serializer.is_valid():
                return self._error(
                    "INVALID_INPUT",
                    "Error creating task! Please confirm all fields have the necessary data.",
                    status_code=status.HTTP_400_BAD_REQUEST,
            )

            task = TaskService.create_task(
                user = request.user,
                project_id= project.id,
                data = serializer.validated_data
            )

            # Return serializer response
            output_serializer = TaskSerializer(task)
            return self._success(data=output_serializer.data, message="Task created successfully", status=status.HTTP_201_CREATED)
        
        else: # GET request
            # List all tasks for this project
            tasks = TaskModel.objects.filter(
                project=project
            ).select_related('created_by', 'assigned_to', 'project')
            
            serializer = TaskSerializer(tasks, many=True)
            return self._success(data=serializer.data, message="Tasks retrieved successfully")
    

    @action(detail=True, methods=['post'], url_path="members")
    def add_members(self, request, pk=None):
        project = self.get_object() # get project id

        serializer = ProjectMemberSerializer(
            data = request.data,
            context = {"request": request}
        )

        # serializer.is_valid(raise_exception=True)
        if not serializer.is_valid():
                return self._error(
                    "INVALID_INPUT",
                    "Unable to add member to project!. Please relaod and try again.",
                    status_code=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save(project=project)

        return self._success(data=serializer.data, message="User added to project.", status = status.HTTP_201_CREATED)
        

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = ExtendedUserSerializer