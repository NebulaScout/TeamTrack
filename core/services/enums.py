from django.db import models

class PriorityEnum(models.TextChoices):
    LOW = 'LOW', 'low'
    MEDIUM = 'MEDIUM', 'medium'
    HIGH =  'HIGH', 'high'

class StatusEnum(models.TextChoices):
    OPEN = 'OPEN', 'open'
    IN_PROGRESS = 'IN_PROGRESS', 'in_progress'
    DONE = 'DONE', 'done'

class TaskFieldEnum(models.TextChoices):
    STATUS = "status", "Status"
    PRIORITY = "priority", "Priority"
    ASSIGNED_TO = "assigned_to", "Assigned To"
    DUE_DATE = "due_date", "Due Date"
    TITLE = "title", "Title"
    DESCRIPTION = "description", "Description"