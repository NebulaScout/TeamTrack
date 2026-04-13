from __future__ import annotations

from typing import Any, Optional

from django.contrib.auth.models import User
from django.db.models import Model
from django.utils import timezone

from audit.models import GlobalAuditLog
from core.services.enums import AuditAction, AuditModule


class AuditService:
    @staticmethod
    def _enum_value(value):
        """
        Return raw value for enums or the original string.
        """
        return getattr(value, "value", value)

    @staticmethod
    def resolve_action_type(*, module, action, metadata=None):
        """
        Canonical action_type used by dashboard endpoints.
        Defaults to: <module>_<action>
        Supports special-cases from metadata.
        """
        metadata = metadata or {}
        module_val = str(AuditService._enum_value(module)).lower()
        action_val = str(AuditService._enum_value(action)).lower()

        # Optional explicit override if caller provides one
        explicit = metadata.get("action_type")
        if explicit:
            return str(explicit)

        # Friendly aliases
        if module_val == "comment" and action_val == "created":
            return "comment_added"

        if module_val == "task" and action_val == "updated":
            changes = metadata.get("changes", {})
            status_change = changes.get("status", {})
            new_status = str(status_change.get("new", "")).upper()
            if new_status == "DONE":
                return "task_completed"
            return "task_updated"

        # Default canonical format
        return f"{module_val}_{action_val}"

    @staticmethod
    def log(
        *,
        module: AuditModule | str,
        action: AuditAction | str,
        actor: Optional[User] = None,
        target: Optional[Model] = None,
        target_type: str = "",
        target_id: Optional[int] = None,
        target_label: str = "",
        project: Optional[Model] = None,
        description: str = "",
        metadata: Optional[dict[str, Any]] = None,
        occurred_at=None,
    ) -> GlobalAuditLog:
        """
        Create one global audit log entry.

        You can pass either:
        - target model instance, or
        - explicit target_type and target_id and target_label.

        project may be passed directly, or inferred from target.project when available.
        """
        resolved_target_type = target_type
        resolved_target_id = target_id
        resolved_target_label = target_label

        if target is not None:
            if not resolved_target_type:
                resolved_target_type = target.__class__.__name__
            if resolved_target_id is None:
                resolved_target_id = getattr(target, "pk", None)
            if not resolved_target_label:
                resolved_target_label = str(target)

            if project is None and hasattr(target, "project"):
                project = getattr(target, "project", None)

        if metadata is None:
            metadata = {}

        if occurred_at is None:
            occurred_at = timezone.now()

        return GlobalAuditLog.objects.create(
            actor=actor,
            module=module,
            action=action,
            target_type=resolved_target_type,
            target_id=resolved_target_id,
            target_label=resolved_target_label,
            project=project,
            description=description,
            metadata=metadata,
            occurred_at=occurred_at,
        )

    @staticmethod
    def created(
        *,
        module: AuditModule | str,
        actor: Optional[User] = None,
        target: Optional[Model] = None,
        project: Optional[Model] = None,
        description: str = "",
        metadata: Optional[dict[str, Any]] = None,
        occurred_at: Optional[str] = None,
    ) -> GlobalAuditLog:
        return AuditService.log(
            module=module,
            action=AuditAction.CREATED,
            actor=actor,
            target=target,
            project=project,
            description=description,
            metadata=metadata,
            occurred_at=occurred_at,
        )

    @staticmethod
    def updated(
        *,
        module: AuditModule | str,
        actor: Optional[User] = None,
        target: Optional[Model] = None,
        project: Optional[Model] = None,
        description: str = "",
        metadata: Optional[dict[str, Any]] = None,
        occurred_at: Optional[str] = None,
    ) -> GlobalAuditLog:
        return AuditService.log(
            module=module,
            action=AuditAction.UPDATED,
            actor=actor,
            target=target,
            project=project,
            description=description,
            metadata=metadata,
            occurred_at=occurred_at,
        )

    @staticmethod
    def deleted(
        *,
        module: AuditModule | str,
        actor: Optional[User] = None,
        target_type: str,
        target_id: Optional[int] = None,
        target_label: str = "",
        project: Optional[Model] = None,
        description: str = "",
        metadata: Optional[dict[str, Any]] = None,
        occurred_at: Optional[str] = None,
    ) -> GlobalAuditLog:
        return AuditService.log(
            module=module,
            action=AuditAction.DELETED,
            actor=actor,
            target_type=target_type,
            target_id=target_id,
            target_label=target_label,
            project=project,
            description=description,
            metadata=metadata,
            occurred_at=occurred_at,
        )

    @staticmethod
    def registered(
        *,
        actor: Optional[User] = None,
        target: Optional[Model] = None,
        description: str = "User registered",
        metadata: Optional[dict[str, Any]] = None,
        occurred_at: Optional[str] = None,
    ) -> GlobalAuditLog:
        return AuditService.log(
            module=AuditModule.USER,
            action=AuditAction.REGISTERED,
            actor=actor,
            target=target,
            description=description,
            metadata=metadata,
            occurred_at=occurred_at,
        )
