from datetime import timedelta
from rest_framework import status

from django.db.models import Count, Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import User, Group

from api.v1.common.responses import ResponseMixin
from core.services.enums import StatusEnum
from core.services.project_service import ProjectService
from projects.models import ProjectMembers, ProjectsModel
from tasks.models import CommentModel, TaskHistoryModel, TaskModel
from accounts.models import RegisterModel
from ..serializers.admin_serializers import (
    AuditLogsResponseSerializer,
    AdminUserSerializer,
    AdminUserUpdateSerializer,
    AdminProjectListSerializer,
    AdminProjectWriteSerializer,
    AdminTaskListSerializer,
    AdminTasksResponseSerializer,
    AdminTaskUpdateSerializer,
    AdminQuickActionsSerializer,
    AdminTaskDetailSerializer,
)
from ..serializers.user_serializers import DashboardSerializer


class AdminQuickActionsView(ResponseMixin, APIView):
    """
    Admin-only dashboard.

    Returns:
    - overdue_tasks  : non-done tasks whose due_date is in the past (up to 20)
    - unassigned_tasks: tasks with no assigned_to, not done (up to 20)
    - recent_activity: platform-wide events — new registrations + task history (up to 20)
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=AdminQuickActionsSerializer)
    def get(self, request):
        if not request.user.is_staff:
            return self._error(
                code="FORBIDDEN",
                message="Admin access required.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        now = timezone.now()
        today = now.date()
        week_ago = now - timedelta(days=7)

        # Overdue tasks (platform-wide, not just user's projects)
        overdue_qs = (
            TaskModel.objects.filter(due_date__lt=today)
            .exclude(status=StatusEnum.DONE)
            .select_related("project", "assigned_to", "assigned_to__profile")
            .order_by("due_date")[:20]
        )
        overdue_tasks = [
            {
                "id": task.pk,
                "title": task.title,
                "project_name": task.project.project_name,
                "due_date": task.due_date,
                "assigned_to": task.assigned_to,
            }
            for task in overdue_qs
        ]

        # Unassigned tasks (platform-wide, not done)
        unassigned_qs = (
            TaskModel.objects.filter(assigned_to__isnull=True)
            .exclude(status=StatusEnum.DONE)
            .select_related("project")
            .order_by("-priority", "due_date")[:20]
        )
        unassigned_tasks = [
            {
                "id": task.pk,
                "title": task.title,
                "project_name": task.project.project_name,
                "priority": task.priority,
            }
            for task in unassigned_qs
        ]

        # Recent platform-wide activity
        activities = []

        # New user registrations in the last 7 days
        registrations = (
            RegisterModel.objects.filter(created_at__gte=week_ago)
            .select_related("user")
            .order_by("-created_at")[:20]
        )
        for reg in registrations:
            full_name = reg.user.get_full_name() or reg.user.username
            activities.append(
                {
                    "id": reg.pk,
                    "action_type": "user_registered",
                    "description": "New user registered",
                    "actor_name": full_name,
                    "actor_url": None,
                    "timestamp": reg.created_at,
                }
            )

        # Task completions across the platform in the last 7 days
        completions = (
            TaskHistoryModel.objects.filter(
                field_changed="status",
                new_value=StatusEnum.DONE,
                timestamp__gte=week_ago,
            )
            .select_related("changed_by", "task")
            .order_by("-timestamp")[:20]
        )
        for history in completions:
            actor = history.changed_by
            full_name = actor.get_full_name() if actor else "Unknown"
            activities.append(
                {
                    "id": history.pk,
                    "action_type": "task_completed",
                    "description": f"completed task \"{history.task.title if history.task else ''}\"",
                    "actor_name": full_name or (actor.username if actor else "Unknown"),
                    "actor_url": None,
                    "timestamp": history.timestamp,
                }
            )

        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        activities = activities[:20]

        payload = {
            "overdue_tasks": overdue_tasks,
            "unassigned_tasks": unassigned_tasks,
            "recent_activity": activities,
        }

        serializer = AdminQuickActionsSerializer(payload)
        return self._success(data=serializer.data)


class AdminUsersView(ResponseMixin, APIView):
    """
    GET  /dashboard/admin/users/  — list all users with search & filters
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]

    @extend_schema(responses=AdminUserSerializer(many=True))
    def get(self, request):
        queryset = (
            User.objects.select_related("profile")
            .prefetch_related("groups")
            .annotate(
                project_count=Count("project_memberships", distinct=True),
                task_count=Count("assigned_tasks", distinct=True),
            )
            .order_by("-date_joined")
        )

        search = request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search)
                | Q(email__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
            )

        role = request.query_params.get("role", "").strip()
        if role:
            queryset = queryset.filter(groups__name=role)

        status_filter = request.query_params.get("status", "").strip()
        if status_filter == "active":
            queryset = queryset.filter(is_active=True)
        elif status_filter == "inactive":
            queryset = queryset.filter(is_active=False)

        serializer = AdminUserSerializer(
            queryset, many=True, context={"request": request}
        )
        return self._success(
            data=serializer.data, message="Users retrieved successfully"
        )


class AdminUserDetailView(ResponseMixin, APIView):
    """
    GET    /dashboard/admin/users/<pk>/  — user detail
    PATCH  /dashboard/admin/users/<pk>/  — update role and/or active status
    DELETE /dashboard/admin/users/<pk>/  — delete user
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]

    def _get_user(self, pk):
        try:
            return (
                User.objects.select_related("profile")
                .prefetch_related("groups")
                .annotate(
                    project_count=Count("project_memberships", distinct=True),
                    task_count=Count("assigned_tasks", distinct=True),
                )
                .get(pk=pk)
            )
        except User.DoesNotExist:
            return None

    @extend_schema(responses=AdminUserSerializer)
    def get(self, request, pk):
        user = self._get_user(pk)
        if not user:
            return self._error(
                "NOT_FOUND", "User not found.", status_code=status.HTTP_404_NOT_FOUND
            )
        serializer = AdminUserSerializer(user, context={"request": request})
        return self._success(data=serializer.data)

    @extend_schema(request=AdminUserUpdateSerializer, responses=AdminUserSerializer)
    def patch(self, request, pk):
        user = self._get_user(pk)
        if not user:
            return self._error(
                "NOT_FOUND", "User not found.", status_code=status.HTTP_404_NOT_FOUND
            )

        if user == request.user:
            return self._error(
                "FORBIDDEN",
                "You cannot modify your own account via this endpoint.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        serializer = AdminUserUpdateSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return self._error(
                "VALIDATION_ERROR",
                "Invalid data.",
                serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data

        if isinstance(data, dict) and "role" in data:
            try:
                group = Group.objects.get(name=data["role"])
            except Group.DoesNotExist:
                return self._error(
                    "NOT_FOUND",
                    f'Role "{data["role"]}" does not exist.',
                    status_code=status.HTTP_404_NOT_FOUND,
                )
            user.groups.clear()
            user.groups.add(group)

        if isinstance(data, dict) and "is_active" in data:
            user.is_active = data["is_active"]
            user.save(update_fields=["is_active"])

        updated_user = self._get_user(pk)
        return self._success(
            data=AdminUserSerializer(updated_user, context={"request": request}).data,
            message="User updated successfully.",
        )

    def delete(self, request, pk):
        user = self._get_user(pk)
        if not user:
            return self._error(
                "NOT_FOUND", "User not found.", status_code=status.HTTP_404_NOT_FOUND
            )

        if user == request.user:
            return self._error(
                "FORBIDDEN",
                "You cannot delete your own account.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        username = user.username
        user.delete()
        return self._success(message=f'User "{username}" deleted successfully.')


class AdminProjectsView(ResponseMixin, APIView):
    """
    GET  /dashboard/admin/projects/   — list all projects (search + status filter)
    POST /dashboard/admin/projects/   — create a new project
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]

    def _base_queryset(self):
        return (
            ProjectsModel.objects.select_related("created_by", "created_by__profile")
            .prefetch_related(
                "members",
                "members__project_member",
                "members__project_member__profile",
            )
            .annotate(
                tasks_total=Count("project_tasks", distinct=True),
                tasks_completed=Count(
                    "project_tasks",
                    filter=Q(project_tasks__status=StatusEnum.DONE),
                    distinct=True,
                ),
                member_count=Count("members", distinct=True),
            )
            .order_by("-created_at")
        )

    @extend_schema(responses=AdminProjectListSerializer(many=True))
    def get(self, request):
        # from .serializers import AdminProjectListSerializer

        queryset = self._base_queryset()

        search = request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(project_name__icontains=search)

        status_filter = request.query_params.get("status", "").strip().upper()
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        serializer = AdminProjectListSerializer(
            queryset, many=True, context={"request": request}
        )
        return self._success(
            data=serializer.data, message="Projects retrieved successfully"
        )

    @extend_schema(
        request=AdminProjectWriteSerializer,
        responses={201: AdminProjectListSerializer},
    )
    def post(self, request):
        # from .serializers import AdminProjectWriteSerializer, AdminProjectListSerializer

        serializer = AdminProjectWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return self._error(
                "INVALID_INPUT",
                "Invalid project data. Please check all required fields.",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        project = ProjectService.create_project(
            user=request.user, data=serializer.validated_data
        )

        # Re-fetch with annotations so the response shape matches the list endpoint
        annotated = self._base_queryset().get(pk=project.pk)
        serializer = AdminProjectListSerializer(annotated, context={"request": request})
        return self._success(
            data=serializer.data,
            message="Project created successfully",
            status_code=status.HTTP_201_CREATED,
        )


class AdminProjectDetailView(ResponseMixin, APIView):
    """
    GET    /dashboard/admin/projects/<pk>/  — project detail
    PATCH  /dashboard/admin/projects/<pk>/  — update project fields
    DELETE /dashboard/admin/projects/<pk>/  — delete project
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]

    def _get_project(self, pk):
        try:
            return (
                ProjectsModel.objects.select_related(
                    "created_by", "created_by__profile"
                )
                .prefetch_related(
                    "members",
                    "members__project_member",
                    "members__project_member__profile",
                )
                .annotate(
                    tasks_total=Count("project_tasks", distinct=True),
                    tasks_completed=Count(
                        "project_tasks",
                        filter=Q(project_tasks__status=StatusEnum.DONE),
                        distinct=True,
                    ),
                    member_count=Count("members", distinct=True),
                )
                .get(pk=pk)
            )
        except ProjectsModel.DoesNotExist:
            return None

    @extend_schema(responses=AdminProjectListSerializer)
    def get(self, request, pk):
        # from .serializers import AdminProjectListSerializer

        project = self._get_project(pk)
        if not project:
            return self._error(
                "NOT_FOUND",
                "Project not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        serializer = AdminProjectListSerializer(project, context={"request": request})
        return self._success(data=serializer.data)

    @extend_schema(
        request=AdminProjectWriteSerializer,
        responses=AdminProjectListSerializer,
    )
    def patch(self, request, pk):
        # from .serializers import AdminProjectWriteSerializer, AdminProjectListSerializer

        project = self._get_project(pk)
        if not project:
            return self._error(
                "NOT_FOUND",
                "Project not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        serializer = AdminProjectWriteSerializer(
            project, data=request.data, partial=True
        )
        if not serializer.is_valid():
            return self._error(
                "INVALID_INPUT",
                "Invalid project data",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save()

        updated = self._get_project(pk)
        out = AdminProjectListSerializer(updated, context={"request": request})
        return self._success(data=out.data, message="Project updated successfully")

    def delete(self, request, pk):
        try:
            project = ProjectsModel.objects.get(pk=pk)
        except ProjectsModel.DoesNotExist:
            return self._error(
                "NOT_FOUND",
                "Project not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        project.delete()
        return self._success(
            message="Project deleted successfully",
            status_code=status.HTTP_204_NO_CONTENT,
        )


class AdminTasksView(ResponseMixin, APIView):
    """
    GET /dashboard/admin/tasks/
    Returns platform-wide (Admin) or project-scoped (Project Manager) task list
    plus summary stats shown in the two cards at the top of the Tasks tab.

    Query params:
      - search   : filters by task title or project name
      - status   : exact match against StatusEnum (TO_DO, IN_PROGRESS, IN_REVIEW, DONE)
      - priority : exact match against PriorityEnum (LOW, MEDIUM, HIGH)
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def _is_authorised(self, user):
        return user.is_staff or user.groups.filter(name="Project Manager").exists()

    def _base_queryset(self, user):
        qs = TaskModel.objects.select_related(
            "project",
            "assigned_to",
            "assigned_to__profile",
        ).order_by("-created_at")
        if user.is_staff:
            return qs  # Admin: all tasks platform-wide
        # Project Manager: only tasks belonging to their projects
        project_ids = list(
            ProjectsModel.objects.filter(
                Q(created_by=user) | Q(members__project_member=user)
            )
            .distinct()
            .values_list("id", flat=True)
        )
        return qs.filter(project_id__in=project_ids)

    @extend_schema(responses=AdminTasksResponseSerializer)
    def get(self, request):

        user = request.user
        if not self._is_authorised(user):
            return self._error(
                "FORBIDDEN",
                "Admin or Project Manager access required.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        today = timezone.now().date()
        base_qs = self._base_queryset(user)

        # Stats (computed before search/filter so the cards always reflect reality)
        overdue_count = (
            base_qs.filter(due_date__lt=today).exclude(status=StatusEnum.DONE).count()
        )
        unassigned_count = (
            base_qs.filter(assigned_to__isnull=True)
            .exclude(status=StatusEnum.DONE)
            .count()
        )

        task_qs = base_qs

        search = request.query_params.get("search", "").strip()
        if search:
            task_qs = task_qs.filter(
                Q(title__icontains=search) | Q(project__project_name__icontains=search)
            )

        status_filter = request.query_params.get("status", "").strip().upper()
        if status_filter:
            task_qs = task_qs.filter(status=status_filter)

        priority_filter = request.query_params.get("priority", "").strip().upper()
        if priority_filter:
            task_qs = task_qs.filter(priority=priority_filter)

        serializer = AdminTaskListSerializer(
            task_qs, many=True, context={"request": request}
        )
        return self._success(
            data={
                "stats": {
                    "overdue_count": overdue_count,
                    "unassigned_count": unassigned_count,
                },
                "tasks": serializer.data,
            }
        )


class AdminTaskDetailView(ResponseMixin, APIView):
    """
    PATCH  /dashboard/admin/tasks/<pk>/
        Update a task's status, priority, or assignee.
        Admin: any task. Project Manager: only tasks in their projects.

    DELETE /dashboard/admin/tasks/<pk>/
        Delete a task.
        Admin: any task. Project Manager: only tasks in their projects.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def _is_authorised(self, user):
        return user.is_staff or user.groups.filter(name="Project Manager").exists()

    def _get_task(self, pk, user):
        """
        Returns (task, None) on success.
        Returns (None, 'not_found') or (None, 'forbidden') on failure.
        """
        try:
            task = (
                TaskModel.objects.select_related(
                    "project",
                    "assigned_to",
                    "assigned_to__profile",
                )
                .prefetch_related(
                    "comments",
                    "comments__author",
                    "comments__author__profile",
                )
                .get(pk=pk)
            )
        except TaskModel.DoesNotExist:
            return None, "not_found"

        if user.is_staff:
            return task, None

        # Project Manager scope check
        project_ids = list(
            ProjectsModel.objects.filter(
                Q(created_by=user) | Q(members__project_member=user)
            )
            .distinct()
            .values_list("id", flat=True)
        )
        if task.project.pk not in project_ids:
            return None, "forbidden"

        return task, None

    @extend_schema(responses=AdminTaskDetailSerializer)
    def get(self, request, pk):
        user = request.user
        if not self._is_authorised(user):
            return self._error(
                "FORBIDDEN",
                "Admin or Project Manager access required.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        task, err = self._get_task(pk, user)
        if err == "not_found":
            return self._error(
                "NOT_FOUND",
                "Task not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if err == "forbidden":
            return self._error(
                "FORBIDDEN",
                "You do not have access to this task.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        return self._success(
            data=AdminTaskDetailSerializer(task, context={"request": request}).data
        )

    @extend_schema(request=AdminTaskUpdateSerializer, responses=AdminTaskListSerializer)
    def patch(self, request, pk):

        user = request.user
        if not self._is_authorised(user):
            return self._error(
                "FORBIDDEN",
                "Admin or Project Manager access required.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        task, err = self._get_task(pk, user)
        if err == "not_found":
            return self._error(
                "NOT_FOUND", "Task not found.", status_code=status.HTTP_404_NOT_FOUND
            )
        if err == "forbidden":
            return self._error(
                "FORBIDDEN",
                "You do not have access to this task.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        serializer = AdminTaskUpdateSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return self._error(
                "VALIDATION_ERROR",
                "Invalid data.",
                serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data or {}

        if task:
            if isinstance(data, dict) and "status" in data:
                task.status = data["status"]
            if isinstance(data, dict) and "priority" in data:
                task.priority = data["priority"]
            if isinstance(data, dict) and "assigned_to" in data:
                if data["assigned_to"] is None:
                    task.assigned_to = None
                else:
                    try:
                        new_assignee = User.objects.get(pk=data["assigned_to"])
                    except User.DoesNotExist:
                        return self._error(
                            "NOT_FOUND",
                            "Assigned user not found.",
                            status_code=status.HTTP_404_NOT_FOUND,
                        )
                    task.assigned_to = new_assignee

            task.save()

            # Re-fetch with relations so the serializer can traverse them
            updated_task = TaskModel.objects.select_related(
                "project", "assigned_to", "assigned_to__profile"
            ).get(pk=task.pk)

            return self._success(
                data=AdminTaskListSerializer(
                    updated_task, context={"request": request}
                ).data,
                message="Task updated successfully.",
            )

    def delete(self, request, pk):
        user = request.user
        if not self._is_authorised(user):
            return self._error(
                "FORBIDDEN",
                "Admin or Project Manager access required.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        task, err = self._get_task(pk, user)
        if err == "not_found" or err == "forbidden":
            return self._error(
                "NOT_FOUND", "Task not found.", status_code=status.HTTP_404_NOT_FOUND
            )

        if task:
            task.delete()
        return self._success(message="Task deleted successfully.")


class AdminAuditLogsView(ResponseMixin, APIView):
    """
    GET /dashboard/admin/audit-logs/

    Returns platform-wide (Admin) or project-scoped (Project Manager) audit logs
    from TaskHistoryModel showing all task changes with comprehensive filtering.

    Query params:
      - search      : filters by task title or project name
      - project     : filter by specific project ID
      - user        : filter by user ID who made the change
      - change_type : filter by field_changed (status, priority, assigned_to, due_date, title, description)
      - limit       : number of results to return (default: 50, max: 200)
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def _is_authorised(self, user):
        return user.is_staff or user.groups.filter(name="Project Manager").exists()

    def _get_action_type(self, field_changed):
        """Convert field_changed enum to user-friendly action type"""
        mapping = {
            "status": "changed status",
            "priority": "changed priority",
            "assigned_to": "assigned",
            "due_date": "changed due date",
            "title": "changed title",
            "description": "changed description",
        }
        return mapping.get(field_changed, "updated")

    def _format_description(self, history):
        """Generate human-readable description of the change"""
        field = history.field_changed
        task_title = history.task.title if history.task else "Unknown task"

        if field == "status":
            return f'changed status "{task_title}"'
        elif field == "priority":
            return f'changed priority "{task_title}"'
        elif field == "assigned_to":
            if history.new_value:
                try:
                    assignee = User.objects.get(username=history.new_value)
                    assignee_name = assignee.get_full_name() or assignee.username
                    return f'assigned "{task_title}" to {assignee_name}'
                except User.DoesNotExist:
                    return f'assigned "{task_title}"'
            return f'unassigned "{task_title}"'
        elif field == "due_date":
            return f'changed due date "{task_title}"'
        elif field == "title":
            return f'changed title from "{history.old_value}" to "{history.new_value}"'
        elif field == "description":
            return f'changed description "{task_title}"'
        else:
            return f'updated "{task_title}"'

    @extend_schema(responses=AuditLogsResponseSerializer)
    def get(self, request):
        user = request.user

        if not self._is_authorised(user):
            return self._error(
                "FORBIDDEN",
                "Admin or Project Manager access required.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        # Base queryset with necessary joins
        base_qs = TaskHistoryModel.objects.select_related(
            "changed_by",
            "changed_by__profile",
            "task",
            "task__project",
        ).order_by("-timestamp")

        # Scope by user role
        if not user.is_staff:
            # Project Manager: only history from their projects
            project_ids = list(
                ProjectsModel.objects.filter(
                    Q(created_by=user) | Q(members__project_member=user)
                )
                .distinct()
                .values_list("id", flat=True)
            )
            base_qs = base_qs.filter(task__project_id__in=project_ids)

        # Apply filters
        search = request.query_params.get("search", "").strip()
        if search:
            base_qs = base_qs.filter(
                Q(task__title__icontains=search)
                | Q(task__project__project_name__icontains=search)
            )

        project_filter = request.query_params.get("project", "").strip()
        if project_filter:
            try:
                project_id = int(project_filter)
                base_qs = base_qs.filter(task__project_id=project_id)
            except ValueError:
                pass

        user_filter = request.query_params.get("user", "").strip()
        if user_filter:
            try:
                user_id = int(user_filter)
                base_qs = base_qs.filter(changed_by_id=user_id)
            except ValueError:
                pass

        change_type_filter = request.query_params.get("change_type", "").strip()
        if change_type_filter:
            base_qs = base_qs.filter(field_changed=change_type_filter)

        # Limit results
        limit = request.query_params.get("limit", "50").strip()
        try:
            limit = min(int(limit), 200)  # Cap at 200
        except ValueError:
            limit = 50

        total_count = base_qs.count()
        history_entries = base_qs[:limit]

        # Format data for serializer
        logs = []
        for history in history_entries:
            if not history.task:  # Skip if task was deleted
                continue

            logs.append(
                {
                    "id": history.pk,
                    "actor": history.changed_by,
                    "action_type": self._get_action_type(history.field_changed),
                    "description": self._format_description(history),
                    "task_id": history.task.pk,
                    "task_title": history.task.title,
                    "project_id": (
                        history.task.project.pk if history.task.project else None
                    ),
                    "project_name": (
                        history.task.project.project_name
                        if history.task.project
                        else "Unknown"
                    ),
                    "field_changed": history.field_changed,
                    "old_value": history.old_value,
                    "new_value": history.new_value,
                    "timestamp": history.timestamp,
                }
            )

        serializer = AuditLogsResponseSerializer(
            {
                "logs": logs,
                "total_count": total_count,
            }
        )

        return self._success(
            data=serializer.data, message="Audit logs retrieved successfully"
        )
