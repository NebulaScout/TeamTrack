from projects.models import ProjectsModel

class ProjectService:
    @staticmethod
    def create_project(*, user, data):
        """Centralized logic for project creation"""
        return ProjectsModel.objects.create(
            created_by=user,
            **data,
        )