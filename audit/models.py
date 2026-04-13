from django.db import models

from django_enum import EnumField
from django.contrib.auth.models import User
from django.utils import timezone
from core.services.enums import AuditAction, AuditModule


class GlobalAuditLog(models.Model):
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="global_audit_logs",
    )

    module = EnumField(AuditModule)
    action = EnumField(AuditAction)

    # Generic target reference
    target_type = models.CharField(max_length=60, blank=True, default="")
    target_id = models.PositiveBigIntegerField(null=True, blank=True)
    target_label = models.CharField(max_length=255, blank=True, default="")

    # Optional project context for filtering/scope
    project = models.ForeignKey(
        "projects.ProjectsModel",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )

    description = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)

    occurred_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-occurred_at"]
        indexes = [
            models.Index(fields=["module", "action", "occurred_at"]),
            models.Index(fields=["target_type", "target_id"]),
            models.Index(fields=["actor", "occurred_at"]),
            models.Index(fields=["project", "occurred_at"]),
        ]

    def __str__(self):
        actor_name = self.actor.username if self.actor else "system"
        return f"{self.module}:{self.action} by {actor_name}"
