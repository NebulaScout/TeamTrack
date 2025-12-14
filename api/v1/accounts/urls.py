from rest_framework.routers import DefaultRouter

from .viewsets import RegisterViewSet, UserViewSet

router = DefaultRouter()
router.register(r'register', RegisterViewSet, basename='register-api')
router.register(r'users', UserViewSet, basename='user-profiles')

urlpatterns = router.urls
