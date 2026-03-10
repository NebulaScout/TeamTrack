from rest_framework.routers import DefaultRouter
from django.urls import path, include

from .views import (
    CalendarEventViewSet,
    ProjectMilestoneViewSet,
    TaskDeadlineSyncViewSet,
    CalendarViewViewSet,
)

router = DefaultRouter()
router.register(r"events", CalendarEventViewSet, basename="calendar-events")
router.register(r"milesones", ProjectMilestoneViewSet, basename="milestones")
router.register(r"deadline-sync", TaskDeadlineSyncViewSet, basename="deadline-sync")
router.register(r"preferences", CalendarViewViewSet, basename="calendar-preferences")

urlpatterns = router.urls
