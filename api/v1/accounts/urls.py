from rest_framework.routers import DefaultRouter

from .viewsets import RegisterViewSet

router = DefaultRouter()
router.register(r'register', RegisterViewSet, basename='register-api')

urlpatterns = router.urls
