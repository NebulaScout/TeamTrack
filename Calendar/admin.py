from django.contrib import admin
from .models import CalendarEvent, ProjectMilestone, TaskDeadlineSync, CalendarView


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "user",
        "event_type",
        "event_date",
        "start_time",
        "priority",
        "linked_task",
        "linked_project",
    ]
    list_filter = ["event_type", "priority", "event_date", "is_recurring"]
    search_fields = ["title", "description", "user__username"]
    date_hierarchy = "event_date"
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("user", "title", "description", "event_type", "priority")},
        ),
        ("Date & Time", {"fields": ("event_date", "start_time", "end_time")}),
        ("Linking", {"fields": ("linked_task", "linked_project")}),
        (
            "Recurrence",
            {
                "fields": ("is_recurring", "recurrence_pattern"),
                "classes": ("collapse",),
            },
        ),
        (
            "Reminders",
            {
                "fields": ("send_reminder", "reminder_minutes_before"),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadata",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(ProjectMilestone)
class ProjectMilestoneAdmin(admin.ModelAdmin):
    list_display = ["title", "project", "due_date", "priority", "status", "is_overdue"]
    list_filter = ["priority", "status", "due_date"]
    search_fields = ["title", "description", "project__project_name"]
    date_hierarchy = "due_date"
    readonly_fields = ["created_at", "updated_at", "is_overdue", "days_until_due"]


@admin.register(TaskDeadlineSync)
class TaskDeadlineSyncAdmin(admin.ModelAdmin):
    list_display = ["task", "auto_sync_enabled", "last_synced"]
    list_filter = ["auto_sync_enabled", "last_synced"]
    search_fields = ["task__title"]
    actions = ["sync_selected_tasks"]

    def sync_selected_tasks(self, request, queryset):
        count = 0
        for sync in queryset:
            sync.sync_to_calendar()
            count += 1
        self.message_user(request, f"Successfully synced {count} tasks to calendar")

    sync_selected_tasks.short_description = "Sync selected tasks to calendar"


@admin.register(CalendarView)
class CalendaViewAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "default_view",
        "show_tasks",
        "show_milestones",
        "show_meetings",
    ]
    list_filter = ["default_view", "show_weekends"]
    search_fields = ["user__username"]
