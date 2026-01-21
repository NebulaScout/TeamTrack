from rest_framework.routers import DefaultRouter

from .viewsets import AuthViewSet

router = DefaultRouter()
router.register(r'', AuthViewSet, basename="auth")

urlpatterns = router.urls
