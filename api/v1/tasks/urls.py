from rest_framework.routers import DefaultRouter

from .viewsets import TaskViewSet

router = DefaultRouter()
router.register(r'', TaskViewSet, basename='project_tasks')

urlpatterns = router.urls