from django.db import models

class PriorityEnum(models.TextChoices):
    LOW = 'LOW', 'low'
    MEDIUM = 'MEDIUM', 'medium'
    HIGH =  'HIGH', 'high'

class StatusEnum(models.TextChoices):
    OPEN = 'OPEN', 'open'
    IN_PROGRESS = 'IN_PROGRESS', 'in_progress'
    DONE = 'DONE', 'done'
