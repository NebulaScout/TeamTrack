from rest_framework.routers import DefaultRouter

from .views import CalendarEventViewSet

router = DefaultRouter()
router.register(r'', CalendarEventViewSet, basename='calendar')

urlpatterns = router.urls
