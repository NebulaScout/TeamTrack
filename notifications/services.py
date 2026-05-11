from __future__ import annotations

from typing import Iterable

from django.db import transaction
from django.contrib.auth.models import User

from audit.models import GlobalAuditLog
from core.services.audit_service import AuditService
from core.services.enums import AuditModule
from projects.models import ProjectMembers
from tasks.models import TaskModel
from notifications.models import (
    Notification,
    NotificationPreference,
    NotificationCategory,
)


class NotificationService:
    @staticmethod
    def _action_type(audit_log: GlobalAuditLog) -> str:
        return AuditService.resolve_action_type(
            module=audit_log.module,
            action=audit_log.action,
            metadata=audit_log.metadata or {},
        )

    @staticmethod
    def _category(audit_log: GlobalAuditLog) -> str:
        module_val = str(audit_log.module)
        if module_val == AuditModule.TASK:
            return NotificationCategory.TASK
        if module_val == AuditModule.PROJECT:
            return NotificationCategory.PROJECT
        if module_val == AuditModule.COMMENT:
            return NotificationCategory.COMMENT
        if module_val == AuditModule.USER:
            return NotificationCategory.USER
        return NotificationCategory.SYSTEM

    @staticmethod
    def _title_and_message(audit_log: GlobalAuditLog) -> tuple[str, str]:
        description = (audit_log.description or "").strip()
        if description:
            title = description[:200]
            return title, description

        module_val = str(audit_log.module)
        action_val = str(audit_log.action)
        title = f"{module_val.title()} {action_val.title()}"
        return title, ""

    @staticmethod
    def _recipient_ids(audit_log: GlobalAuditLog) -> set[int]:
        recipients: set[int] = set()
        metadata = audit_log.metadata or {}

        def _project_member_ids(project_id: int) -> set[int]:
            return set(
                ProjectMembers.objects.filter(project_id=project_id).values_list(
                    "project_member_id", flat=True
                )
            )

        project_id = getattr(audit_log, "project_id", None)

        # Project-scoped: all members of the project
        if project_id:
            recipients.update(_project_member_ids(project_id))

        # Task-specific: assigned user and creator
        if str(audit_log.module) == AuditModule.TASK:
            assigned_to_id = metadata.get("assigned_to_id")
            if assigned_to_id:
                recipients.add(int(assigned_to_id))

            task_id = metadata.get("task_id") or audit_log.target_id
            if task_id:
                task = (
                    TaskModel.objects.select_related("created_by", "assigned_to")
                    .filter(pk=task_id)
                    .first()
                )
                task_created_by_id = (
                    getattr(task, "created_by_id", None) if task else None
                )
                if task_created_by_id:
                    recipients.add(task_created_by_id)
                task_assigned_to_id = (
                    getattr(task, "assigned_to_id", None) if task else None
                )
                if task_assigned_to_id:
                    recipients.add(task_assigned_to_id)

                # If audit log didn't include project, derive it from task
                if not project_id and task and getattr(task, "project_id", None):
                    project_id = task.project.pk

        # Comment-specific: notify task creator and assignee
        if str(audit_log.module) == AuditModule.COMMENT:
            task_id = metadata.get("task_id")
            if task_id:
                task = (
                    TaskModel.objects.select_related("created_by", "assigned_to")
                    .filter(pk=task_id)
                    .first()
                )
                task_created_by_id = (
                    getattr(task, "created_by_id", None) if task else None
                )
                if task_created_by_id:
                    recipients.add(task_created_by_id)
                task_assigned_to_id = (
                    getattr(task, "assigned_to_id", None) if task else None
                )
                if task_assigned_to_id:
                    recipients.add(task_assigned_to_id)

                if not project_id and task and getattr(task, "project_id", None):
                    project_id = task.project.pk

        # User-specific: notify the target user (e.g., registered)
        if str(audit_log.module) == AuditModule.USER:
            if audit_log.target_id:
                recipients.add(int(audit_log.target_id))

        # Enforce project membership if project context exists
        if project_id:
            recipients &= _project_member_ids(project_id)

        # Avoid self notifications
        actor_id = getattr(audit_log, "actor_id", None)
        if actor_id:
            recipients.discard(actor_id)

        return recipients

    @staticmethod
    def _is_allowed(
        *,
        preference: NotificationPreference | None,
        module_val: str,
        action_type: str,
        project_id: int | None,
    ) -> bool:
        if preference is None:
            return True
        if not preference.enabled:
            return False
        if module_val in (preference.muted_modules or []):
            return False
        if action_type in (preference.muted_action_types or []):
            return False
        if project_id and project_id in (preference.muted_project_ids or []):
            return False
        return True

    @staticmethod
    def create_from_audit(audit_log: GlobalAuditLog) -> int:
        recipient_ids = NotificationService._recipient_ids(audit_log)
        if not recipient_ids:
            return 0

        prefs = NotificationPreference.objects.filter(user_id__in=recipient_ids)
        prefs_by_user = {int(pref.user.pk): pref for pref in prefs}

        module_val = str(audit_log.module)
        action_type = NotificationService._action_type(audit_log)
        category = NotificationService._category(audit_log)
        title, message = NotificationService._title_and_message(audit_log)
        project = getattr(audit_log, "project", None)
        project_id = getattr(project, "pk", None)

        notifications: list[Notification] = []
        actor_id = getattr(audit_log, "actor_id", None)
        for user_id in recipient_ids:
            preference = prefs_by_user.get(user_id)
            if not NotificationService._is_allowed(
                preference=preference,
                module_val=module_val,
                action_type=action_type,
                project_id=project_id,
            ):
                continue

            notifications.append(
                Notification(
                    recipient_id=user_id,
                    actor_id=actor_id,
                    project_id=project_id,
                    audit_log=audit_log,
                    category=category,
                    title=title,
                    message=message,
                    action_url="",
                    metadata={
                        **(audit_log.metadata or {}),
                        "action_type": action_type,
                        "module": module_val,
                    },
                )
            )

        if not notifications:
            return 0

        with transaction.atomic():
            Notification.objects.bulk_create(notifications)

        return len(notifications)
