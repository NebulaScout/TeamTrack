from projects.models import ProjectsModel, ProjectMembers

class ProjectService:
    @staticmethod
    def create_project(*, user, data):
        # Create a project
        project = ProjectsModel.objects.create(
            created_by=user,
            **data,
        )
    
        # Add the creator as a member of the project
        ProjectMembers.objects.create(
            project = project,
            project_member = user,
            role_in_project = "Project Manager" # creator of project is always a project manager
        )

        return project

    # @staticmethod
    # def add_members(*, data):
    #     """Add users to a project and their respective roles"""
    #     return ProjectMembers.objects.create()