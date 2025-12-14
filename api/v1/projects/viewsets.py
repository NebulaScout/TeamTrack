from rest_framework import viewsets

from projects.models import ProjectsModel
from .serializers import ProjectsSerializer

class ProjectsViewSet(viewsets.ModelViewSet):
    queryset = ProjectsModel.objects.all()
    serializer_class = ProjectsSerializer