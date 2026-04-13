from django.db import models


class PriorityEnum(models.TextChoices):
    LOW = "LOW", "low"
    MEDIUM = "MEDIUM", "medium"
    HIGH = "HIGH", "high"


class StatusEnum(models.TextChoices):
    TO_DO = "TO_DO", "to_do"
    IN_PROGRESS = "IN_PROGRESS", "in_progress"
    IN_REVIEW = "IN_REVIEW", "in_review"
    DONE = "DONE", "done"


class EventTypesEnum(models.TextChoices):
    MEETING = "MEETING", "Meeting"
    TASK = "TASK", "Task"
    DEADLINE = "DEADLINE", "Deadline"
    REMINDER = "REMINDER", "Reminder"


class TaskFieldEnum(models.TextChoices):
    """Fields tracked in task history"""

    STATUS = "status", "Status"
    PRIORITY = "priority", "Priority"
    ASSIGNED_TO = "assigned_to", "Assigned To"
    DUE_DATE = "due_date", "Due Date"
    TITLE = "title", "Title"
    DESCRIPTION = "description", "Description"


class RoleEnum(models.TextChoices):
    """User roles"""

    ADMIN = "Admin", "Admin"
    PROJECT_MANAGER = "Project Manager", "Project Manager"
    DEVELOPER = "Developer", "Developer"
    GUEST = "Guest", "Guest"


class ProjectStatusEnum(models.TextChoices):
    """Fields for a project's status"""

    ACTIVE = "ACTIVE", "active"
    COMPLETED = "COMPLETED", "completed"
    ON_HOLD = "ON_HOLD", "on_hold"


class RecurrenceEnums(models.TextChoices):
    """Calendar recurrence"""

    DAILY = "DAILY", "Daily"
    WEEKLY = "WEEKLY", "Weekly"
    MONTHLY = "MONTHLY", "Monthly"


class AuditModule(models.TextChoices):
    """Modules being logged"""

    PROJECT = "project", "Project"
    TASK = "task", "Task"
    USER = "user", "User"
    COMMENT = "comment", "Comment"
    SYSTEM = "system", "System"


class AuditAction(models.TextChoices):
    """User actions"""

    CREATED = "created", "Created"
    UPDATED = "updated", "Updated"
    DELETED = "deleted", "Deleted"
    REGISTERED = "registered", "Registered"
