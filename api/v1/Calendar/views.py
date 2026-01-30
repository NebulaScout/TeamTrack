from django.shortcuts import render
from rest_framework import viewsets

from Calendar.models import CalendarEvent
from .serializers import CalendarEventSerializer
from core.services.permissions import CalendarEventPermissions

class CalendarEventViewSet(viewsets.ModelViewSet):
    serializer_class = CalendarEventSerializer
    permission_classes = [CalendarEventPermissions]

    def get_queryset(self): # type: ignore
        return CalendarEvent.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
