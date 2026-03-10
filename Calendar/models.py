from django.db import models
from django.conf import settings
from django_enum import EnumField
from django.utils import timezone
from datetime import datetime

from core.services.enums import (
    EventTypesEnum,
    PriorityEnum,
    StatusEnum,
    RecurrenceEnums,
)
from projects.models import ProjectsModel
from tasks.models import TaskModel


def current_time():
    return timezone.now().time()


def current_date():
    return timezone.now().date()


class CalendarEvent(models.Model):
    """Main calendar event model. Can be standalone or linked to tasks/ projects"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="calendar_events",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    event_type = EnumField(EventTypesEnum, default=EventTypesEnum.TASK)
    priority = EnumField(PriorityEnum, null=True, blank=True)

    # Date & time fields
    event_date = models.DateField(default=current_date)
    start_time = models.TimeField(default=current_time)
    end_time = models.TimeField(default=current_time)

    # Optional linking to tasks/projects
    linked_task = models.ForeignKey(
        TaskModel,
        on_delete=models.CASCADE,
        related_name="calendar_events",
        null=True,
        blank=True,
        help_text="Link this event to a specific task",
    )
    linked_project = models.ForeignKey(
        ProjectsModel,
        on_delete=models.CASCADE,
        related_name="calendar_events",
        null=True,
        blank=True,
        help_text="Link this event to a specific project",
    )

    # Recurrence support
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = EnumField(RecurrenceEnums, null=True, blank=True)

    # Notifications settings
    send_reminder = models.BooleanField(default=False)
    reminder_minutes_before = models.IntegerField(default=30, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["event_date", "start_time"]
        indexes = [
            models.Index(fields=["event_date", "user"]),
            models.Index(fields=["linked_task"]),
            models.Index(fields=["linked_project"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.event_date}"

    @property
    def is_overdue(self):
        """Check if event is in the past"""
        now = timezone.now()
        event_datetime = timezone.make_aware(
            timezone.datetime.combine(self.event_date, self.start_time)
        )
        return event_datetime < now

    @property
    def duration_minutes(self):
        """Calculate event duration in minutes"""
        if self.end_time and self.start_time:
            delta = datetime.combine(
                datetime.min.date(), self.end_time
            ) - datetime.combine(datetime.min.date(), self.start_time)
            return int(delta.total_seconds() / 60)
        return 0


class ProjectMilestone(models.Model):
    """Major milestones/deadlines for projects"""

    project = models.ForeignKey(
        ProjectsModel, on_delete=models.CASCADE, related_name="milestones"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    due_date = models.DateField()
    priority = EnumField(PriorityEnum, default=PriorityEnum.MEDIUM)
    status = EnumField(StatusEnum, default=StatusEnum.TO_DO)

    # Auto create calendar events for milestones
    create_calendar_event = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_milestones",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["due_date"]
        indexes = [models.Index(fields=["project", "due_date"])]

    def __str__(self):
        return f"{self.project.project_name} - {self.title}"

    @property
    def is_overdue(self):
        """Check of milestone is overdue"""
        return self.due_date < timezone.now().date() and self.status != StatusEnum.DONE

    @property
    def days_until_due(self):
        """Calculate days unitl milestone is due"""
        delta = self.due_date - timezone.now().date()
        return delta.days

    def save(self, *args, **kwargs):
        """Auto-create calendar events for project members when milestone is created"""
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new and self.create_calendar_event:
            # create calendar events for all project members
            from projects.models import ProjectMembers

            project_members = ProjectMembers.objects.filter(project=self.project)

            for member in project_members:
                CalendarEvent.objects.get_or_create(
                    user=member.project_member,
                    linked_project=self.project,
                    event_date=self.due_date,
                    event_type=EventTypesEnum.DEADLINE,
                    defaults={
                        "title": f"Milestone: {self.title}",
                        "description": self.description,
                        "priority": self.priority,
                        "start_time": timezone.now().time(),
                        "end_time": timezone.now().time(),
                    },
                )


class TaskDeadlineSync(models.Model):
    """
    Automatically sync task due dates to calendar events.
    This creates a calendar event when a task has a due date
    """

    task = models.OneToOneField(
        TaskModel,
        on_delete=models.CASCADE,
        related_name="deadline_sync",
        primary_key=True,
    )
    auto_sync_enabled = models.BooleanField(default=True)
    last_synced = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Deadline sync for {self.task.title}"

    def sync_to_calendar(self):
        """Create or update calendar event for task deadline"""
        if not self.auto_sync_enabled or not self.task.due_date:
            return

        if self.task.assigned_to:
            calendar_event, created = CalendarEvent.objects.get_or_create(
                user=self.task.assigned_to,
                linked_task=self.task,
                defaults={
                    "title": f"Task Deadline: {self.task.title}",
                    "description": self.task.description or "",
                    "event_type": EventTypesEnum.DEADLINE,
                    "priority": self.task.priority,
                    "start_time": timezone.now().time(),
                    "end_time": timezone.now().time(),
                    "send_reminder": True,
                    "reminder_minutes_before": 1440,  # 24hours before
                },
            )

            if not created:
                # update existing
                calendar_event.title = f"Task Deadline: {self.task.title}"
                calendar_event.description = self.task.description or ""
                calendar_event.event_date = self.task.due_date
                calendar_event.priority = self.task.priority
                calendar_event.save()


class CalendarView(models.Model):
    """user's personal calendar view preferences"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="calendar_preferences",
    )
    default_view = models.CharField(
        max_length=20,
        choices=[
            ("DAY", "Day"),
            ("WEEK", "Week"),
            ("MONTH", "Month"),
            ("AGENDA", "Agenda"),
        ],
        default="WEEK",
    )
    show_weekends = models.BooleanField(default=True)

    # Fitler preferences
    show_tasks = models.BooleanField(default=True)
    show_milestones = models.BooleanField(default=True)
    show_meetings = models.BooleanField(default=True)

    # Project filters - store as JSON or use ManyToMany
    filtered_projects = models.ManyToManyField(
        ProjectsModel, blank=True, related_name="calendar_filters"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Calendar preferences for {self.user.username}"
