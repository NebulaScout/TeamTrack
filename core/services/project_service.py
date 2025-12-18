from projects.models import ProjectsModel, ProjectMembers

class ProjectService:
    @staticmethod
    def create_project(*, user, data):
        """Centralized logic for project creation"""
        return ProjectsModel.objects.create(
            created_by=user,
            members = user,
            **data,
        )
    # @staticmethod
    # def add_members(*, data):
    #     """Add users to a project and their respective roles"""
    #     return ProjectMembers.objects.create()