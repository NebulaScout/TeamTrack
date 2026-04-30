from datetime import timedelta

from django.contrib.auth.models import User
from django.db.models import Count
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from api.v1.common.responses import ResponseMixin
from core.services.enums import PriorityEnum, ProjectStatusEnum, StatusEnum
from core.services.permissions import IsAdminDashboardUser
from projects.models import ProjectsModel
from tasks.models import TaskHistoryModel, TaskModel
from ..serializers.admin_serializers import AdminAnalyticsResponseSerializer


class AdminAnalyticsView(ResponseMixin, APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminDashboardUser]

    def _window_days(self, request) -> int:
        window = request.query_params.get("window", "30").strip()
        if window == "7":
            return 7
        return 30

    def _period_label(self, window_days: int) -> str:
        return "last week" if window_days == 7 else "last month"

    def _pct_change(self, current: int, previous: int) -> float | None:
        if previous == 0:
            return None
        return round((current - previous) / previous * 100, 1)

    def _change_block(self, current: int, previous: int, label: str) -> dict:
        pct = self._pct_change(current, previous)
        if pct is None:
            return {"change": f"N/A from {label}", "positive": True}
        sign = "+" if pct >= 0 else ""
        return {"change": f"{sign}{pct}% from {label}", "positive": pct >= 0}

    def _avatar_url(self, user: User | None, request) -> str | None:
        if not user:
            return None
        if hasattr(user, "profile") and user.profile and user.profile.avatar:  # type: ignore
            return request.build_absolute_uri(user.profile.avatar.url)  # type: ignore
        return None

    def _status_name(self, value: str | None) -> str:
        mapping = {
            StatusEnum.TO_DO: "Open",
            StatusEnum.IN_PROGRESS: "In Progress",
            StatusEnum.IN_REVIEW: "In Review",
            StatusEnum.DONE: "Completed",
        }
        if value is not None:
            try:
                status_enum = StatusEnum(value)
                if status_enum in mapping:
                    return mapping[status_enum]
            except (ValueError, KeyError):
                pass
        return "Unknown"

    def _is_admin_user(self, user: User) -> bool:
        return (
            user.is_superuser
            or user.is_staff
            or user.groups.filter(name="Admin").exists()
        )

    def _is_project_manager(self, user: User) -> bool:
        return user.groups.filter(name="Project Manager").exists()

    def _projects_queryset(self, user: User):
        if self._is_admin_user(user):
            return ProjectsModel.objects.all()
        if self._is_project_manager(user):
            return ProjectsModel.objects.filter(created_by=user)
        return ProjectsModel.objects.none()

    @extend_schema(responses=AdminAnalyticsResponseSerializer)
    def get(self, request):
        window_days = self._window_days(request)
        label = self._period_label(window_days)

        now = timezone.now()
        today = now.date()
        window_start = now - timedelta(days=window_days)
        prev_start = window_start - timedelta(days=window_days)
        prev_end = window_start

        projects_qs = self._projects_queryset(request.user)
        tasks_qs = TaskModel.objects.filter(project__in=projects_qs)
        history_qs = TaskHistoryModel.objects.filter(task__project__in=projects_qs)

        total_current = tasks_qs.filter(
            created_at__gte=window_start, created_at__lt=now
        ).count()
        total_prev = tasks_qs.filter(
            created_at__gte=prev_start, created_at__lt=prev_end
        ).count()

        completed_current = history_qs.filter(
            field_changed="status",
            new_value=StatusEnum.DONE,
            timestamp__gte=window_start,
            timestamp__lt=now,
        ).count()
        completed_prev = history_qs.filter(
            field_changed="status",
            new_value=StatusEnum.DONE,
            timestamp__gte=prev_start,
            timestamp__lt=prev_end,
        ).count()

        overdue_current = (
            tasks_qs.filter(due_date__lt=today).exclude(status=StatusEnum.DONE).count()
        )
        overdue_prev = (
            tasks_qs.filter(due_date__lt=(today - timedelta(days=window_days)))
            .exclude(status=StatusEnum.DONE)
            .count()
        )

        active_current = projects_qs.filter(
            status=ProjectStatusEnum.ACTIVE,
            updated_at__gte=window_start,
            updated_at__lt=now,
        ).count()
        active_prev = projects_qs.filter(
            status=ProjectStatusEnum.ACTIVE,
            updated_at__gte=prev_start,
            updated_at__lt=prev_end,
        ).count()

        analytics_stats = []
        change = self._change_block(total_current, total_prev, label)
        analytics_stats.append(
            {
                "title": "Total Tasks",
                "value": str(total_current),
                "change": change["change"],
                "positive": change["positive"],
            }
        )
        change = self._change_block(completed_current, completed_prev, label)
        analytics_stats.append(
            {
                "title": "Completed Tasks",
                "value": str(completed_current),
                "change": change["change"],
                "positive": change["positive"],
            }
        )
        change = self._change_block(overdue_current, overdue_prev, label)
        analytics_stats.append(
            {
                "title": "Overdue Tasks",
                "value": str(overdue_current),
                "change": change["change"],
                "positive": change["positive"],
            }
        )
        change = self._change_block(active_current, active_prev, label)
        analytics_stats.append(
            {
                "title": "Active Projects",
                "value": str(active_current),
                "change": change["change"],
                "positive": change["positive"],
            }
        )

        status_counts = tasks_qs.values("status").annotate(value=Count("id")).order_by()
        status_map = {row["status"]: row["value"] for row in status_counts}
        tasks_by_status = []
        for status in StatusEnum:
            tasks_by_status.append(
                {
                    "name": self._status_name(status),
                    "value": status_map.get(status, 0),
                }
            )

        priority_counts = (
            tasks_qs.filter(priority__isnull=False)
            .values("priority")
            .annotate(value=Count("id"))
            .order_by()
        )
        priority_map = {row["priority"]: row["value"] for row in priority_counts}
        tasks_by_priority = []
        for priority in PriorityEnum:
            tasks_by_priority.append(
                {
                    "name": priority.label.title(),
                    "value": priority_map.get(priority, 0),
                }
            )

        weeks_count = 1 if window_days == 7 else 4
        weekly_progress = []
        for idx in range(weeks_count):
            week_end = now - timedelta(days=7 * (weeks_count - 1 - idx))
            week_start = week_end - timedelta(days=7)

            completed = history_qs.filter(
                field_changed="status",
                new_value=StatusEnum.DONE,
                timestamp__gte=week_start,
                timestamp__lt=week_end,
            ).count()

            pending = (
                tasks_qs.filter(
                    created_at__gte=week_start,
                    created_at__lt=week_end,
                )
                .exclude(status=StatusEnum.DONE)
                .count()
            )

            weekly_progress.append(
                {
                    "week": f"Week {idx + 1}",
                    "completed": completed,
                    "pending": pending,
                }
            )

        top_n = 5
        created_rows = (
            tasks_qs.filter(
                created_at__gte=window_start,
                created_at__lt=now,
                created_by__isnull=False,
            )
            .values("created_by")
            .annotate(created=Count("id"))
        )
        created_map = {row["created_by"]: row["created"] for row in created_rows}

        completed_rows = (
            history_qs.filter(
                field_changed="status",
                new_value=StatusEnum.DONE,
                timestamp__gte=window_start,
                timestamp__lt=now,
                changed_by__isnull=False,
            )
            .values("changed_by")
            .annotate(completed=Count("id"))
        )
        completed_map = {row["changed_by"]: row["completed"] for row in completed_rows}

        activity_scores = {}
        for user_id, count in created_map.items():
            activity_scores[user_id] = activity_scores.get(user_id, 0) + count
        for user_id, count in completed_map.items():
            activity_scores[user_id] = activity_scores.get(user_id, 0) + count

        top_activity_ids = [
            user_id
            for user_id, _ in sorted(
                activity_scores.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        ][:top_n]

        activity_users = (
            User.objects.filter(id__in=top_activity_ids)
            .select_related("profile")
            .in_bulk(top_activity_ids)
        )

        most_active_users = []
        for user_id in top_activity_ids:
            user = activity_users.get(user_id)
            if not user:
                continue
            most_active_users.append(
                {
                    "id": user.pk,
                    "name": user.get_full_name() or user.username,
                    "created": created_map.get(user_id, 0),
                    "completed": completed_map.get(user_id, 0),
                    "avatar": self._avatar_url(user, request),
                }
            )

        assignments = (
            tasks_qs.filter(
                assigned_to__isnull=False,
                created_at__gte=window_start,
                created_at__lt=now,
            )
            .values("assigned_to")
            .annotate(tasks=Count("id"))
            .order_by("-tasks")[:top_n]
        )

        assignment_ids = [row["assigned_to"] for row in assignments]
        assignment_users = (
            User.objects.filter(id__in=assignment_ids)
            .select_related("profile")
            .in_bulk(assignment_ids)
        )

        users_with_most_assignments = []
        for row in assignments:
            user = assignment_users.get(row["assigned_to"])
            if not user:
                continue
            users_with_most_assignments.append(
                {
                    "id": user.pk,
                    "name": user.get_full_name() or user.username,
                    "tasks": row["tasks"],
                    "avatar": self._avatar_url(user, request),
                }
            )

        projects = (
            projects_qs.annotate(members_count=Count("members"))
            .order_by("-members_count")
            .values("project_name", "members_count")[:top_n]
        )
        projects_by_team_size = [
            {"name": row["project_name"], "members": row["members_count"]}
            for row in projects
        ]

        payload = {
            "analytics_stats": analytics_stats,
            "tasks_by_status": tasks_by_status,
            "tasks_by_priority": tasks_by_priority,
            "weekly_task_progress": weekly_progress,
            "most_active_users": most_active_users,
            "users_with_most_assignments": users_with_most_assignments,
            "projects_by_team_size": projects_by_team_size,
        }

        serializer = AdminAnalyticsResponseSerializer(payload)
        return self._success(data=serializer.data)
