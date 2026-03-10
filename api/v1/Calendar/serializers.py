from rest_framework import serializers
from datetime import datetime, timedelta
from django.utils import timezone

from Calendar.models import (
    CalendarEvent,
    ProjectMilestone,
    TaskDeadlineSync,
    CalendarView,
)
from tasks.models import TaskModel
from projects.models import ProjectsModel


class TaskSummarySerializer(serializers.ModelSerializer):
    """Minimal task info for calendar display"""

    project_name = serializers.CharField(source="project.project_name", read_only=True)
    assigned_to_username = serializers.CharField(
        source="assigned_to.username", read_only=True
    )

    class Meta:
        model = TaskModel
        fields = [
            "id",
            "title",
            "status",
            "priority",
            "due_date",
            "project_name",
            "assigned_to_username",
        ]


class ProjectSummarySerializer(serializers.ModelSerializer):
    """Minimal project info for calendar display"""

    created_by_username = serializers.CharField(
        source="created_by.username", read_only=True
    )

    class Meta:
        model = ProjectsModel
        fields = [
            "id",
            "project_name",
            "status",
            "priority",
            "start_date",
            "end_date",
            "created_by_username",
        ]


class CalendarEventSerializer(serializers.ModelSerializer):
    """Main calendar event serializer with linked tasks and project details"""

    linked_task_details = TaskSummarySerializer(source="linked_task", read_only=True)
    linked_project_details = ProjectSummarySerializer(
        source="linked_project", read_only=True
    )
    username = serializers.CharField(source="user.username", read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    duration_minutes = serializers.IntegerField(read_only=True)

    class Meta:
        model = CalendarEvent
        fields = [
            "id",
            "title",
            "description",
            "event_type",
            "priority",
            "event_date",
            "start_time",
            "end_time",
            "linked_task",
            "linked_task_details",
            "linked_project",
            "linked_project_details",
            "is_recurring",
            "recurrence_pattern",
            "send_reminder",
            "reminder_minutes_before",
            "username",
            "is_overdue",
            "duration_minutes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "username"]

    def validate(self, attrs):
        """Validate event times and dates"""
        start_time = attrs.get("start_time")
        end_time = attrs.get("end_time")

        if start_time and end_time and end_time < start_time:
            raise serializers.ValidationError("End time must be after start time")
        return attrs


class ProjectMilestoneSerializer(serializers.ModelSerializer):
    """Project milestone serializer"""

    project_name = serializers.CharField(source="project.project_name", read_only=True)
    created_by_username = serializers.CharField(
        source="created_by.username", read_only=True
    )
    is_overdue = serializers.BooleanField(read_only=True)
    days_until_due = serializers.IntegerField(read_only=True)

    class Meta:
        model = ProjectMilestone
        fields = [
            "id",
            "project",
            "project_name",
            "title",
            "description",
            "due_date",
            "priority",
            "status",
            "create_calendar_event",
            "created_by",
            "created_by_username",
            "is_overdue",
            "days_until_due",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

        def validate_due_date(self, value):
            """Ensure due date is not in the past"""
            if value < timezone.now().date():
                raise serializers.ValidationError(
                    "Milestone due date cannot be in the past"
                )
            return value


class TaskDeadlineSyncSerializer(serializers.ModelSerializer):
    """Task deadline sync configuration"""

    task_title = serializers.CharField(source="task.title", read_only=True)
    task_due_date = serializers.DateField(source="task.due_date", read_only=True)

    class Meta:
        model = TaskDeadlineSync
        fields = [
            "task",
            "task_title",
            "task_due_date",
            "aut_sync_enabled",
            "last_synced",
        ]
        read_only_fields = ["last_synced"]


class CalendarViewSerializer(serializers.ModelSerializer):
    """User calendar view preferences"""

    filtered_project_names = serializers.SerializerMethodField()

    class Meta:
        model = CalendarView
        fields = [
            "id",
            "default_view",
            "show_weekends",
            "show_tasks",
            "show_milestones",
            "show_meetings",
            "filtered_projects",
            "filtered_project_names",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_filtered_project_names(self, obj):
        return [p.project_name for p in obj.filtered_projects.all()]


class CalendarTimelineSerializer(serializers.Serializer):
    """Aggregated timeline view combining events, tasks, and milestones"""

    date = serializers.DateField()
    events = CalendarEventSerializer(many=True, read_only=True)
    task_deadlines = TaskSummarySerializer(many=True, read_only=True)
    milestones = ProjectMilestoneSerializer(many=True, read_only=True)

    class Meta:
        fields = ["date", "events", "task_deadlines", "milestones"]


class CalendarOverviewSerializer(serializers.Serializer):
    """High-level calendar overview with statistics"""

    date_range = serializers.DictField()
    total_events = serializers.IntegerField()
    total_task_deadlines = serializers.IntegerField()
    total_milestones = serializers.IntegerField()
    upcoming_deadlines = serializers.ListField()
    overdue_items = serializers.ListField()
    events_by_priority = serializers.DictField()
    events_by_type = serializers.DictField()
