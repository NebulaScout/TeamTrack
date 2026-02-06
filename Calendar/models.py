from django.db import models
from django.conf import settings
from django_enum import EnumField
from django.utils import timezone

from core.services.enums import EventTypesEnum, PriorityEnum

def current_time():
    return timezone.now().time()

def current_date():
    return timezone.now().date()

class CalendarEvent(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='calendar_events')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    event_type = EnumField(EventTypesEnum, null=True, blank=True)
    priority = EnumField(PriorityEnum, null=True, blank=True)
    event_date = models.DateField(default=current_date)
    start_time = models.TimeField(default=current_time)
    end_time = models.TimeField(default=current_time)
    created_at = models.DateTimeField(auto_now_add=True)
    # updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
