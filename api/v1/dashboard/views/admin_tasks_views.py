from datetime import timedelta
from rest_framework import status
from drf_spectacular.utils import extend_schema

from django.db.models import Q
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import User

from api.v1.common.responses import ResponseMixin
from core.services.enums import StatusEnum
from projects.models import ProjectsModel
from tasks.models import TaskHistoryModel, TaskModel
from accounts.models import RegisterModel
from ..serializers.admin_serializers import (
    AdminTaskListSerializer,
    AdminTasksResponseSerializer,
    AdminTaskUpdateSerializer,
    AdminQuickActionsSerializer,
    AdminTaskDetailSerializer,
)


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
                "project_id": task.project.pk,
                "project_name": task.project.project_name,
                "priority": task.priority,
            }
            for task in unassigned_qs
        ]

        activities = []

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
            return qs
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
