from rest_framework.routers import DefaultRouter

from .viewsets import NotificationViewSet, NotificationPreferenceViewSet

router = DefaultRouter()
router.register(r"", NotificationViewSet, basename="notifications")
router.register(
    r"preferences", NotificationPreferenceViewSet, basename="notification-preferences"
)

urlpatterns = router.urls
