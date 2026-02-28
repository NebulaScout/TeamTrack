from rest_framework import viewsets, status, permissions
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from django.db.models import Q
from rest_framework.decorators import action

from .serializers import (
    TaskHistorySerializer,
    CommentSerializer,
    CommentWriteSerializer,
    TaskDetailSerializer,
    TaskListSerializer,
    TaskWriteSerializer,
)
from tasks.models import TaskModel, CommentModel, TaskHistoryModel
from core.services.roles import ROLE_PERMISSIONS
from core.services.permissions import TaskPermissions
from core.services.task_service import TaskService, CommentService


class CommentViewSet(viewsets.ModelViewSet):
    pass


class TaskViewSet(viewsets.ModelViewSet):
    permission_classes = [TaskPermissions]
    authentication_classes = [JWTAuthentication]

    def get_serializer_class(self):  # type: ignore
        """Return appropriate serializer based on action"""
        if self.action == "list":
            return TaskListSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return TaskWriteSerializer
        elif self.action in ["retrieve", "assign"]:
            return TaskDetailSerializer
        return TaskDetailSerializer

    def get_queryset(self):  # type: ignore
        user = self.request.user

        # Base queryset optimization based on action
        queryset = TaskModel.objects.filter(
            Q(created_by=user) | Q(assigned_to=user)
        ).distinct()

        # Optimize based on action
        if self.action == "list":
            # minimal fetching for list view
            return queryset.select_related("project")
        elif self.action == "retrieve":
            # related data for detail view
            return queryset.select_related(
                "created_by", "created_by__profile", "assigned_to__profile", "project"
            ).prefetch_related(
                "comments", "comments__author", "comments__author__profile"
            )
        elif self.action == "assign":
            return queryset.select_related(
                "created_by",
                "created_by__profile",
                "assigned_to",
                "assigned_to__profile",
                "project",
            )
        elif self.action == "task_logs":
            # Include history for logs
            return queryset.select_related("project").prefetch_related(
                "history", "history__changed_by", "history__changed_by__profile"
            )
        else:
            return queryset.select_related("project")

    # TODO: Figure out how to add project in the API structure
    def create(self, request, *args, **kwargs):
        """Create a new task using the task service"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Extract project id from the request data
        project_id = request.data.get("project")

        if not project_id:
            return Response(
                {"error": f"{project_id} field is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # create task model using the service
        task = TaskService.create_task(
            user=request.user, project_id=project_id, data=serializer.validated_data
        )

        # Return with detail serializer to show full created task
        output_serializer = TaskDetailSerializer(task)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    # TODO: Implement PUT /api/v1/project/{project_id}/tasks/{task_id} — update a task (e.g., change description, due date)
    # TODO: GET /api/v1/projects/{project_id}/tasks?status=OPEN&assigned_to=12 - filtering
    #! TODO: Get rid of the patches

    def retrieve(self, request, *args, **kwargs):
        """Get task details with comments"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """update a task"""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        output_serializer = TaskDetailSerializer(instance)
        return Response(output_serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """Partial update a task"""
        kwargs["partial"] = True
        return self.partial_update(request, *args, **kwargs)

    @action(detail=True, methods=["patch"])
    def assign(self, request, pk=None):
        """Assign a task to a user"""
        task = self.get_object()
        assigned_to_id = request.data.get("assigned_to")

        update_task = TaskService.assign_task(
            task_id=task.id,
            altered_by=request.user,
            assigned_to_id=assigned_to_id,
        )

        serializer = self.get_serializer(update_task)
        return Response(serializer.data)

    @action(detail=True, methods=["post", "get"], url_path="comments")
    def comments(self, request, pk=None):
        """Handle comments for a task"""

        # get task id from the url parameter
        task = self.get_object()

        if request.method == "POST":
            # Create a new comment
            serializer = CommentWriteSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            comment = CommentService.create_comment(
                user=request.user, task=task, data=serializer.validated_data
            )

            # Return with full serializer response
            output_serializer = CommentSerializer(comment)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)

        else:  # GET request
            # List all comments for this task
            comments = CommentModel.objects.filter(task=task).select_related(
                "author", "author__profile"
            )

            serializer = CommentSerializer(comments, many=True)
            return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="logs")
    def task_logs(self, request, pk=None):
        """Manage task logs"""
        task = self.get_object()

        task_history = TaskHistoryModel.objects.filter(task=task).select_related(
            "changed_by", "changed_by__profile"
        )
        serializer = TaskHistorySerializer(task_history, many=True)

        return Response(serializer.data)
