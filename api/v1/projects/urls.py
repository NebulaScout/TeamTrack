from django.urls import path
from rest_framework.routers import DefaultRouter

from .viewsets import ProjectsViewSet

router = DefaultRouter()
router.register(r'projects', ProjectsViewSet, basename='team-projects')

urlpatterns = router.urls