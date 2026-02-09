from rest_framework.routers import DefaultRouter
from django.urls import path, include

from .viewsets import RegisterAPIView, UserViewSet, TeamUserViewSet

router = DefaultRouter()
# router.register(r'register', RegisterViewSet, basename='register-api')
router.register(r'users', UserViewSet, basename='user-profiles')
router.register(r'team/users', TeamUserViewSet, basename='team-users')

urlpatterns = [
    path('', include(router.urls,)),
    path('register/', RegisterAPIView.as_view(), name='register'),
]   
