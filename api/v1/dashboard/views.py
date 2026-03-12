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
from .serializers import (
    ActivitySerializer,
    DashboardSerializer,
    DashboardStatsSerializer,
    ProjectProgressSerializer,
    UpcomingDeadlineSerializer,
    AdminUserSerializer,
    AdminUserUpdateSerializer,
    AdminProjectListSerializer,
    AdminProjectMemberSerializer,
    AdminProjectOwnerSerializer,
    AdminProjectWriteSerializer,
)


def _pct_change(current: int, previous: int) -> float | None:
    """Return percentage change vs previous period, None if previous is zero."""
    if previous == 0:
        return None
    return round((current - previous) / previous * 100, 1)


class DashboardView(ResponseMixin, APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=DashboardSerializer)
    def get(self, request):
        user = request.user
        now = timezone.now()
        today = now.date()
        week_ago = now - timedelta(days=7)
        two_weeks_ago = now - timedelta(days=14)

        # Resolve which projects the user can see
        user_project_ids = list(
            ProjectsModel.objects.filter(
                Q(created_by=user) | Q(members__project_member=user)
            )
            .distinct()
            .values_list("id", flat=True)
        )

        # Base task queryset for the user's projects
        base_qs = TaskModel.objects.filter(project_id__in=user_project_ids)

        # Stats
        def _stat(qs_current, qs_previous):
            current = qs_current.count()
            previous = qs_previous.count()
            return {"total": current, "change_pct": _pct_change(current, previous)}

        total_current = base_qs
        total_previous = base_qs.filter(created_at__lt=week_ago)

        completed_current = base_qs.filter(status=StatusEnum.DONE)
        completed_previous = base_qs.filter(
            status=StatusEnum.DONE, updated_at__lt=week_ago
        )

        in_progress_current = base_qs.filter(status=StatusEnum.IN_PROGRESS)
        in_progress_previous = base_qs.filter(
            status=StatusEnum.IN_PROGRESS, updated_at__lt=week_ago
        )

        overdue_current = base_qs.filter(due_date__lt=today).exclude(
            status=StatusEnum.DONE
        )
        overdue_previous = base_qs.filter(
            due_date__lt=(today - timedelta(days=7))
        ).exclude(status=StatusEnum.DONE)

        stats = {
            "total_tasks": _stat(total_current, total_previous),
            "completed": _stat(completed_current, completed_previous),
            "in_progress": _stat(in_progress_current, in_progress_previous),
            "overdue": _stat(overdue_current, overdue_previous),
        }

        # Project progress
        projects = (
            ProjectsModel.objects.filter(id__in=user_project_ids)
            .annotate(
                total_tasks=Count("project_tasks"),
                completed_tasks=Count(
                    "project_tasks",
                    filter=Q(project_tasks__status=StatusEnum.DONE),
                ),
            )
            .order_by("-updated_at")[:10]
        )

        project_progress = []
        for project in projects:
            total = getattr(project, "total_tasks", 0)
            completed = getattr(project, "completed_tasks", 0)
            project_progress.append(
                {
                    "id": project.pk,
                    "project_name": project.project_name,
                    "total_tasks": total,
                    "completed_tasks": completed,
                    "progress_pct": round(completed / total * 100, 1) if total else 0.0,
                }
            )

        # Recent activity
        activities = []

        # Task completions (status changed to DONE in the last 7 days)
        completions = (
            TaskHistoryModel.objects.filter(
                task__project_id__in=user_project_ids,
                field_changed="status",
                new_value=StatusEnum.DONE,
                timestamp__gte=week_ago,
            )
            .select_related(
                "changed_by",
                "changed_by__profile",
                "task",
                "task__project",
            )
            .order_by("-timestamp")[:20]
        )
        for history in completions:
            activities.append(
                {
                    "id": history.pk,
                    "actor": history.changed_by,
                    "action_type": "task_completed",
                    "description": "completed task",
                    "target_name": history.task.title if history.task else "",
                    "target_id": history.task.pk if history.task else None,
                    "timestamp": history.timestamp,
                }
            )

        # Comments added in the last 7 days
        comments = (
            CommentModel.objects.filter(
                task__project_id__in=user_project_ids,
                created_at__gte=week_ago,
            )
            .select_related(
                "author",
                "author__profile",
                "task",
                "task__project",
            )
            .order_by("-created_at")[:20]
        )
        for comment in comments:
            activities.append(
                {
                    "id": comment.pk,
                    "actor": comment.author,
                    "action_type": "comment_added",
                    "description": "commented on",
                    "target_name": comment.task.title if comment.task else "",
                    "target_id": comment.task.pk if comment.task else None,
                    "timestamp": comment.created_at,
                }
            )

        # Members joining projects in the last 7 days
        # ProjectMembers doesn't have a created_at, but TaskHistoryModel tracks
        # "assigned_to" changes — we use that as "joined project" signal if desired.
        # Alternatively, surface general task-update history entries.
        task_updates = (
            TaskHistoryModel.objects.filter(
                task__project_id__in=user_project_ids,
                timestamp__gte=week_ago,
            )
            .exclude(field_changed="status", new_value=StatusEnum.DONE)
            .select_related(
                "changed_by",
                "changed_by__profile",
                "task",
                "task__project",
            )
            .order_by("-timestamp")[:20]
        )
        for history in task_updates:
            activities.append(
                {
                    "id": history.pk,
                    "actor": history.changed_by,
                    "action_type": "task_updated",
                    "description": "updated task",
                    "target_name": history.task.title if history.task else "",
                    "target_id": history.task.pk if history.task else None,
                    "timestamp": history.timestamp,
                }
            )

        # Sort all activity events by timestamp descending, take top 20
        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        activities = activities[:20]

        #  Upcoming deadlines
        deadline_tasks = (
            TaskModel.objects.filter(
                project_id__in=user_project_ids,
                due_date__gte=today,
                due_date__lte=today + timedelta(days=30),
            )
            .exclude(status=StatusEnum.DONE)
            .select_related(
                "project",
                "assigned_to",
                "assigned_to__profile",
            )
            .order_by("due_date", "-priority")[:10]
        )

        # ? Check this out
        upcoming_deadlines = [
            {
                "id": task.pk,
                "title": task.title,
                "project_name": task.project.project_name,
                "due_date": task.due_date,
                "priority": task.priority,
                "assigned_to": task.assigned_to,
            }
            for task in deadline_tasks
        ]

        # serialize payload
        payload = {
            "stats": stats,
            "project_progress": project_progress,
            "recent_activity": activities,
            "upcoming_deadlines": upcoming_deadlines,
        }

        serializer = DashboardSerializer(payload)
        return self._success(data=serializer.data)


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

    def get(self, request):
        if not request.user.is_staff:
            return self._error(
                code="FORBIDDEN",
                message="Admin access required.",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        from .serializers import AdminQuickActionsSerializer

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
