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

    @staticmethod
    def _serialize_value(value):
        if value is None:
            return ""
        return str(value)

    @staticmethod
    def update_project(*, user, project_id, data):
        project = ProjectsModel.objects.get(id=project_id)
        changed_fields = {}

        for field, new_value in data.items():
            old_value = getattr(project, field)
            old_serialized = ProjectService._serialize_value(old_value)
            new_serialized = ProjectService._serialize_value(new_value)

            if old_serialized != new_serialized:
                changed_fields[field] = {
                    "old": old_serialized,
                    "new": new_serialized,
                }

            setattr(project, field, new_value)

        project.save()

        if changed_fields:
            AuditService.updated(
                module=AuditModule.PROJECT,
                actor=user,
                target=project,
                project=project,
                description=f'Updated project "{project.project_name}"',
                metadata={
                    "project_id": project.pk,
                    "project_name": project.project_name,
                    "status": str(project.status) if project.status else "",
                    "priority": str(project.priority) if project.priority else "",
                    "start_date": str(project.start_date) if project.start_date else "",
                    "end_date": str(project.end_date) if project.end_date else "",
                    "changes": changed_fields,
                },
            )

        return project
