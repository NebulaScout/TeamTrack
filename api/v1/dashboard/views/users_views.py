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
from ..serializers.user_serializers import (
    DashboardSerializer,
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
                due_date__lte=today + timedelta(days=100),
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
