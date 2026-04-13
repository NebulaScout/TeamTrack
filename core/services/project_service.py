from projects.models import ProjectsModel, ProjectMembers
from core.services.audit_service import AuditService
from core.services.enums import AuditModule


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
            project=project,
            project_member=user,
            role_in_project="Project Manager",  # creator of project is always a project manager
        )

        AuditService.created(
            module=AuditModule.PROJECT,
            actor=user,
            target=project,
            project=project,
            description=f'Created project "{project.project_name}"',
            metadata={
                "project_name": project.project_name,
                "status": str(project.status) if project.status else "",
                "priority": str(project.priority) if project.priority else "",
                "start_date": str(project.start_date) if project.start_date else "",
                "end_date": str(project.end_date) if project.end_date else "",
            },
        )

        return project

    # @staticmethod
    # def add_members(*, data):
    #     """Add users to a project and their respective roles"""
    #     return ProjectMembers.objects.create()
