from rest_framework import status
from drf_spectacular.utils import (
    extend_schema,
)

from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import User

from api.v1.common.responses import ResponseMixin
from projects.models import ProjectsModel
from tasks.models import TaskHistoryModel
from ..serializers.admin_serializers import (
    AuditLogsResponseSerializer,
)
from .admin_users_views import AdminUsersView, AdminUserDetailView
from .admin_projects_views import (
    AdminProjectMembersView,
    AdminProjectsView,
    AdminProjectDetailView,
)
from .admin_tasks_views import (
    AdminQuickActionsView,
    AdminTasksView,
    AdminTaskDetailView,
)


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
