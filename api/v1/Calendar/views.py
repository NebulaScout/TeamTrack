from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q, Count, Prefetch
from datetime import datetime, timedelta


from Calendar.models import (
    CalendarEvent,
    ProjectMilestone,
    TaskDeadlineSync,
    CalendarView,
)
from tasks.models import TaskModel
from projects.models import ProjectsModel, ProjectMembers

from .serializers import (
    CalendarEventSerializer,
    ProjectMilestoneSerializer,
    TaskDeadlineSyncSerializer,
    CalendarViewSerializer,
    CalendarTimelineSerializer,
    CalendarOverviewSerializer,
    TaskSummarySerializer,
)

# from core.services.permissions import CalendarEventPermissions


class CalendarEventViewSet(viewsets.ModelViewSet):
    """Calendar event viewset with advanced filtering and timeline views"""

    serializer_class = CalendarEventSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "description"]
    ordering_fields = ["event_date", "start_time", "priority", "created_at"]
    ordering = ["event_date", "start_time"]

    def get_queryset(self):  # type: ignore
        queryset = (
            CalendarEvent.objects.filter(user=self.request.user)
            .select_related("linked_task", "linked_project", "linked_task__project")
            .prefetch_related("linked_task_project")
        )

        # Filter by date range
        start_date = self.request.query_params.get("start_date")  # type: ignore
        end_date = self.request.query_params.get("end_date")  # type: ignore

        if start_date:
            queryset = queryset.filter(event_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(event_date__lte=end_date)

        # filter by event type
        event_type = self.request.query_params.get("event_type")  # type: ignore
        if event_type:
            queryset = queryset.filter(event_type=event_type)

        # filter by priority
        priority = self.request.query_params.get("priority")  # type: ignore
        if priority:
            queryset = queryset.filter(priority=priority)

        # filter by project
        project_id = self.request.query_params.get("project_id")  # type: ignore
        if project_id:
            queryset = queryset.filter(
                Q(linked_project_id=project_id) | Q(linked_task__project_id=project_id)
            )

        # show only upcoming events
        upcoming_only = self.request.query_params.get("upcoming_only", "false")  # type: ignore
        if upcoming_only.lower() == "true":
            queryset = queryset.filter(event_date__gte=timezone.now().date())

        return queryset

    def perform_create(self, serializer):
        """Auto-assign event to current user"""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"])
    def timeline(self, request):
        """
        Get aggregated timeline view with events, tasks, and milestones
        Query params: start_date, end_date (default: current week)
        """

        # parse date range
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        if not start_date:
            start_date = timezone.now().date()
        else:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()

        if not end_date:
            end_date = start_date + timedelta(days=7)
        else:
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        # get events in date range
        events = CalendarEvent.objects.filter(
            user=request.user, event_date__gte=start_date, event_date__lte=end_date
        ).select_related("linked_task", "linked_project")

        # get user's projects
        user_projects = ProjectsModel.objects.filter(
            members__project_member=request.user
        )

        # get milestone for user's projects
        milestones = ProjectMilestone.objects.filter(
            project__in=user_projects, due_date__gte=start_date, due_date__lte=end_date
        ).select_related("project")

        # get tasks with deadlines for user
        tasks = TaskModel.objects.filter(
            Q(assigned_to=request.user) | Q(project__in=user_projects),
            due_date__gte=start_date,
            due_date__lte=end_date,
        ).select_related("project", "assigned_to")

        # organize by date
        timeline_data = []
        current_date = start_date

        while current_date <= end_date:
            day_events = events.filter(event_date=current_date)
            day_milestones = milestones.filter(due_date=current_date)
            day_tasks = tasks.filter(due_date=current_date)

            timeline_data.append(
                {
                    "date": current_date,
                    "events": CalendarEventSerializer(day_events, many=True).data,
                    "milestones": ProjectMilestoneSerializer(
                        day_milestones, many=True
                    ).data,
                    "task_deadlines": TaskSummarySerializer(day_tasks, many=True).data,
                }
            )

            current_date += timedelta(days=1)

        return Response(timeline_data)

    @action(detail=False, methods=["get"])
    def overview(self, request):
        """
        Get calendar overview with statistics
        Query params: days_ahead (default: 30)
        """
        days_ahead = int(request.query_params.get("days_ahead", 30))
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=days_ahead)

        # get events
        events = CalendarEvent.objects.filter(
            user=request.user,
            event_date__gte=start_date,
            event_date__lte=end_date,
        )

        # get user's projects
        user_projects = ProjectsModel.objects.filter(
            members__project_member=request.user
        )

        # get tasks
        tasks = TaskModel.objects.filter(
            assigned_to=request.user, due_date__gte=start_date, due_date__lte=end_date
        )

        # get milestones
        milestones = ProjectMilestone.objects.filter(
            project__in=user_projects, due_date__gte=start_date, due_date__lte=end_date
        )

        # claculate statistics
        overdue_tasks = TaskModel.objects.filter(
            assigned_to=request.user,
            due_date__lt=start_date,
            status__in=["TO_DO", "IN_PROGRESS"],
        )

        overdue_milestones = ProjectMilestone.objects.filter(
            project__in=user_projects,
            due_date__lt=start_date,
            status__in=["TO_DO", "IN_PROGRESS"],
        )

        # events by priority
        events_by_priority = {}
        for priority in ["LOW", "MEDIUM", "HIGH"]:
            events_by_priority[priority] = events.filter(priority=priority).count()

        # events by type
        events_by_type = {}
        for event_type in ["MEETING", "TASK", "DEADLINE", "REMINDER"]:
            events_by_type[event_type] = events.filter(event_type=event_type).count()

        overview_data = {
            "date_range": {"start": start_date, "end": end_date, "days": days_ahead},
            "total_events": events.count(),
            "total_task_deadlines": tasks.count(),
            "total_milestones": milestones.count(),
            "upcomeing_deadlines": {
                "next_7_days": tasks.filter(
                    due_date__lte=start_date + timedelta(days=7)
                ).count(),
                "next_14_days": tasks.filter(
                    due_date__lte=start_date + timedelta(days=14)
                ).count(),
                "next_30_days": tasks.count(),
            },
            "overdue_items": {
                "tasks": TaskSummarySerializer(overdue_tasks, many=True).data,
                "milestones": ProjectMilestoneSerializer(
                    overdue_milestones, many=True
                ).data,
            },
            "events_by_priority": events_by_priority,
            "events_by_type": events_by_type,
        }

        return Response(overview_data)

    @action(detail=False, methods=["get"])
    def upcoming_deadlines(self, request):
        """Get all upcoming deadlines (tasks + milestones) in chronological order"""
        days_ahead = int(request.query_params.get("days_ahead", 14))
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=days_ahead)

        # get user's projects
        user_projects = ProjectsModel.objects.filter(
            members__project_member=request.user
        )

        # get tasks
        tasks = (
            TaskModel.objects.filter(
                assigned_to=request.user,
                due_date__gte=start_date,
                due_date__lte=end_date,
            )
            .select_related("project")
            .order_by("due_date")
        )

        # get milestones
        milestones = (
            ProjectMilestone.objects.filter(
                project__in=user_projects,
                due_date__gte=start_date,
                due_date__lte=end_date,
            )
            .select_related("project")
            .order_by("due_date")
        )

        # combine and serialize
        deadlines = {
            "tasks": TaskSummarySerializer(tasks, many=True).data,
            "milestones": ProjectMilestoneSerializer(milestones, many=True).data,
        }

        return Response(deadlines)

    @action(detail=False, methods=["post"])
    def sync_task_deadlines(self, request):
        """Manually trigger sync of all task deadlines to calendar"""
        tasks = TaskModel.objects.filter(
            assigned_to=request.user, due_date__isnull=False
        )

        synced_count = 0
        for task in tasks:
            sync, created = TaskDeadlineSync.objects.get_or_create(task=task)
            sync.sync_to_calendar()
            synced_count += 1

        return Response(
            {
                "message": f"Successfully synced {synced_count} task deadlines to calendar",
                "synced_count": synced_count,
            }
        )


class ProjectMilestoneViewSet(viewsets.ModelViewSet):
    """Project milestone viewset"""

    serializer_class = ProjectMilestoneSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "description"]
    ordering_fields = ["due_date", "priority", "status"]
    ordering = ["due_date"]

    def get_queryset(self):  # type: ignore
        """Get milestones for projects the user is a member of"""
        user_projects = ProjectsModel.objects.filter(
            members__project_member=self.request.user
        )

        queryset = ProjectMilestone.objects.filter(
            project__in=user_projects
        ).select_related("project", "created_by")

        # filter by project
        project_id = self.request.query_params.get("project_id")  # type: ignore
        if project_id:
            queryset = queryset.filter(project_id=project_id)

        # filter by status
        milestone_status = self.request.query_params.get("status")  # type: ignore
        if milestone_status:
            queryset = queryset.filter(status=milestone_status)

        # show only upcoming
        upcoming_only = self.request.query_params.get("upcoming_only", "false")  # type: ignore
        if upcoming_only.lower() == "true":
            queryset = queryset.filter(due_date__gte=timezone.now().date())

        return queryset

    def perform_create(self, serializer):
        """Auto-assign created_by to current user"""
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=["get"])
    def overdue(self, request):
        """Get all overdue milestones"""
        user_projects = ProjectsModel.objects.filter(
            members__project_member=request.user
        )

        overdue_milestones = ProjectMilestone.objects.filter(
            project__in=user_projects,
            due_date__lt=timezone.now().date(),
            status__in=["TO_DO", "IN_PROGRESS"],
        ).select_related("project")

        serializer = self.get_serializer(overdue_milestones, many=True)
        return Response(serializer.data)


class TaskDeadlineSyncViewSet(viewsets.ModelViewSet):
    """Task Deadline Sync ViewSet - manage auto-sync settings"""

    serializer_class = TaskDeadlineSyncSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):  # type: ignore
        """Get deadline syncs for user's tasks"""
        return TaskDeadlineSync.objects.filter(
            task__assigned_to=self.request.user
        ).select_related("task")

    @action(detail=True, methods=["post"])
    def sync_now(self, request, pk=None):
        """Manually trigger sync for a specific task"""
        sync = self.get_object()
        sync.sync_to_calendar()

        return Response(
            {
                "message": f'Synced task "{sync.task.title}" to calendar',
                "last_synced": sync.last_synced,
            }
        )


class CalendarViewViewSet(viewsets.ModelViewSet):
    """Calendar View Preferences ViewSet"""

    serializer_class = CalendarViewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):  # type: ignore
        """Get calendar preferences for current user"""
        return CalendarView.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Auto-assign to current user"""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"])
    def my_preferences(self, request):
        """Get or create preferences for current user"""
        preferences, created = CalendarView.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(preferences)
        return Response(serializer.data)
