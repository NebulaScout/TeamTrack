from django.db import models
from django.conf import settings
from django_enum import EnumField

from core.services.enums import EventTypesEnum, PriorityEnum

class CalendarEvent(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='calendar_events')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    event_type = EnumField(EventTypesEnum, null=True, blank=True)
    priority = EnumField(PriorityEnum, null=True, blank=True)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
