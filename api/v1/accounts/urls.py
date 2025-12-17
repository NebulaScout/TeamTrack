from django.urls import path
from rest_framework.routers import DefaultRouter

from .viewsets import RegisterViewSet, UserViewSet

router = DefaultRouter()
router.register(r'register', RegisterViewSet, basename='register-api')
router.register(r'users', UserViewSet, basename='user-profiles')

urlpatterns = router.urls
    # path('assign_role/', AssignUserRoleViewSet, base_name='assign_role'),
    
