from rest_framework import status
from drf_spectacular.utils import extend_schema

from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import User

from api.v1.common.responses import ResponseMixin
from projects.models import ProjectsModel

# from tasks.models import TaskHistoryModel
from audit.models import GlobalAuditLog
from ..serializers.admin_serializers import AuditLogsResponseSerializer


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

    @extend_schema(responses=AuditLogsResponseSerializer)
    def get(self, request):
        user = request.user

        if not self._is_authorised(user):
            return self._error(
                "FORBIDDEN",
                "Admin or Project Manager access required.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        base_qs = GlobalAuditLog.objects.select_related(
            "actor",
            "actor__profile",
            "project",
        ).order_by("-occurred_at")

        if not user.is_staff:
            project_ids = list(
                ProjectsModel.objects.filter(
                    Q(created_by=user) | Q(members__project_member=user)
                )
                .distinct()
                .values_list("id", flat=True)
            )
            base_qs = base_qs.filter(project_id__in=project_ids)

        search = request.query_params.get("search", "").strip()
        if search:
            base_qs = base_qs.filter(
                Q(description__icontains=search)
                | Q(target_label__icontains=search)
                | Q(project__project_name__icontains=search)
            )

        project_filter = request.query_params.get("project", "").strip()
        if project_filter:
            try:
                project_id = int(project_filter)
                base_qs = base_qs.filter(project_id=project_id)
            except ValueError:
                pass

        user_filter = request.query_params.get("user", "").strip()
        if user_filter:
            try:
                user_id = int(user_filter)
                base_qs = base_qs.filter(actor_id=user_id)
            except ValueError:
                pass

        module_filter = request.query_params.get("module", "").strip().lower()
        if module_filter:
            base_qs = base_qs.filter(module=module_filter)

        action_filter = request.query_params.get("action", "").strip().lower()
        if action_filter:
            base_qs = base_qs.filter(action=action_filter)

        limit = request.query_params.get("limit", "50").strip()
        try:
            limit = min(int(limit), 200)
        except ValueError:
            limit = 50

        total_count = base_qs.count()
        entries = base_qs[:limit]

        logs = []
        for entry in entries:
            logs.append(
                {
                    "id": entry.pk,
                    "actor": entry.actor,
                    "module": entry.module,
                    "action": entry.action,
                    "action_type": f"{entry.module}_{entry.action}",
                    "description": entry.description
                    or f"{entry.action} {entry.module}",
                    "target_type": entry.target_type,
                    "target_id": entry.target_id,
                    "target_label": entry.target_label,
                    "project_id": entry.project.id if entry.project else None,
                    "project_name": (
                        entry.project.project_name if entry.project else None
                    ),
                    "metadata": entry.metadata or {},
                    "timestamp": entry.occurred_at,
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
