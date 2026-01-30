from django.db import models

class PriorityEnum(models.TextChoices):
    LOW = 'LOW', 'low'
    MEDIUM = 'MEDIUM', 'medium'
    HIGH =  'HIGH', 'high'

class StatusEnum(models.TextChoices):
    TO_DO = 'TO_DO', 'to_do'
    IN_PROGRESS = 'IN_PROGRESS', 'in_progress'
    IN_REVIEW = 'IN_REVIEW', 'in_review'
    DONE = 'DONE', 'done'

class EventTypesEnum(models.TextChoices):
    MEETING =  'meeting', 'Meeting'
    TASK = 'task', 'Task'
    DEADLINE = 'deadline', 'Deadline'
    REMINDER = 'reminder', 'Reminder'

class TaskFieldEnum(models.TextChoices):
    """Fields tracked in task history"""
    STATUS = "status", "Status"
    PRIORITY = "priority", "Priority"
    ASSIGNED_TO = "assigned_to", "Assigned To"
    DUE_DATE = "due_date", "Due Date"
    TITLE = "title", "Title"
    DESCRIPTION = "description", "Description"