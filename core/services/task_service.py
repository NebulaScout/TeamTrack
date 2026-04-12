from django.contrib.auth.models import User

from tasks.models import TaskModel, CommentModel, TaskHistoryModel
from projects.models import ProjectsModel
from core.services.audit_service import AuditService
from .enums import TaskFieldEnum, AuditModule


class TaskService:
    TRACKED_FIELDS = {
        "status": TaskFieldEnum.STATUS,
        "priority": TaskFieldEnum.PRIORITY,
        "assigned_to": TaskFieldEnum.ASSIGNED_TO,
        "due_date": TaskFieldEnum.DUE_DATE,
        "title": TaskFieldEnum.TITLE,
        "description": TaskFieldEnum.DESCRIPTION,
    }

    @staticmethod
    def _serialize_value(field, value):
        """
        Normalize values before persisting in TaskHistoryModel.
        Keep strings stable so dashboard formatting/filtering works.
        """
        if field == "assigned_to":
            if value is None:
                return ""
            if isinstance(value, User):
                return value.username
            return str(value)

        if value is None:
            return ""
        return str(value)

    @staticmethod
    def _record_change(*, task, changed_by, field_enum, old_value, new_value):
        TaskHistoryModel.objects.create(
            task=task,
            changed_by=changed_by,
            field_changed=field_enum,
            old_value=old_value,
            new_value=new_value,
        )

    @staticmethod
    def create_task(*, user, project_id, data):
        project = ProjectsModel.objects.get(id=project_id)
        task = TaskModel.objects.create(
            project=project,
            created_by=user,
            **data,
        )

        AuditService.created(
            module=AuditModule.TASK,
            actor=user,
            target=task,
            project=project,
            description=f'Created task "{task.title}"',
            metadata={
                "task_title": task.title,
                "status": str(task.status) if task.status else "",
                "priority": str(task.priority) if task.priority else "",
                "assigned_to_id": task.assigned_to.pk if task.assigned_to else None,
                "due_date": str(task.due_date) if task.due_date else "",
                "project_id": project.pk,
                "project_name": project.project_name,
            },
        )

        return task

    @staticmethod
    def update_task(*, user, task_id, data):
        """
        Generic audited update for all tracked task fields.
        Expects validated serializer data.
        """
        task = TaskModel.objects.get(id=task_id)

        for field, new_val in data.items():
            if field not in TaskService.TRACKED_FIELDS:
                setattr(task, field, new_val)
                continue

            old_val = getattr(task, field)
            old_serialized = TaskService._serialize_value(field, old_val)
            new_serialized = TaskService._serialize_value(field, new_val)

            if old_serialized != new_serialized:
                TaskService._record_change(
                    task=task,
                    changed_by=user,
                    field_enum=TaskService.TRACKED_FIELDS[field],
                    old_value=old_serialized,
                    new_value=new_serialized,
                )

            setattr(task, field, new_val)

        task.save()
        return task

    @staticmethod
    def assign_task(*, altered_by, task_id, assigned_to_id):
        task = TaskModel.objects.get(id=task_id)

        new_user = None
        if assigned_to_id is not None:
            new_user = User.objects.get(id=assigned_to_id)

        old_serialized = TaskService._serialize_value("assigned_to", task.assigned_to)
        new_serialized = TaskService._serialize_value("assigned_to", new_user)

        if old_serialized != new_serialized:
            TaskService._record_change(
                task=task,
                changed_by=altered_by,
                field_enum=TaskFieldEnum.ASSIGNED_TO,
                old_value=old_serialized,
                new_value=new_serialized,
            )

        task.assigned_to = new_user
        task.save()
        return task

    @staticmethod
    def update_task_status(*, user, task_id, status):
        task = TaskModel.objects.get(id=task_id)
        old_serialized = TaskService._serialize_value("status", task.status)
        new_serialized = TaskService._serialize_value("status", status)

        if old_serialized != new_serialized:
            TaskService._record_change(
                task=task,
                changed_by=user,
                field_enum=TaskFieldEnum.STATUS,
                old_value=old_serialized,
                new_value=new_serialized,
            )

        task.status = status
        task.save()
        return task

    @staticmethod
    def update_task_priority(*, user, task_id, priority):
        task = TaskModel.objects.get(id=task_id)
        old_serialized = TaskService._serialize_value("priority", task.priority)
        new_serialized = TaskService._serialize_value("priority", priority)

        if old_serialized != new_serialized:
            TaskService._record_change(
                task=task,
                changed_by=user,
                field_enum=TaskFieldEnum.PRIORITY,
                old_value=old_serialized,
                new_value=new_serialized,
            )

        task.priority = priority
        task.save()
        return task


class CommentService:
    @staticmethod
    def create_comment(*, user, task, data):
        task = TaskModel.objects.get(id=task.id)
        comment = CommentModel.objects.create(
            task=task,
            author=user,
            **data,
        )

        AuditService.created(
            module=AuditModule.COMMENT,
            actor=user,
            target=comment,
            project=task.project,
            description=f'Added comment on task "{task.title}"',
            metadata={
                "comment_id": comment.pk,
                "task_id": task.pk,
                "task_title": task.title,
                "project_id": task.project.pk,
                "project_name": task.project.project_name if task.project else "",
                "content_preview": (comment.content or "")[:120],
            },
        )

        return comment
