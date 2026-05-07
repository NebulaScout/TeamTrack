from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from audit.models import GlobalAuditLog
from projects.models import ProjectsModel
from core.services.enums import NotificationCategory


class Notification(models.Model):
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_notifications",
    )
    project = models.ForeignKey(
        ProjectsModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    audit_log = models.ForeignKey(
        GlobalAuditLog,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )

    category = models.CharField(
        max_length=24,
        choices=NotificationCategory.choices,
        default=NotificationCategory.SYSTEM,
    )
    title = models.CharField(max_length=200)
    message = models.TextField(blank=True, default="")
    action_url = models.CharField(max_length=500, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)

    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
            models.Index(fields=["recipient", "created_at"]),
            models.Index(fields=["category", "created_at"]),
        ]

    def mark_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])

    def mark_unread(self):
        if self.is_read:
            self.is_read = False
            self.read_at = None
            self.save(update_fields=["is_read", "read_at"])


class NotificationPreference(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="notification_preferences"
    )
    enabled = models.BooleanField(default=True)

    # Simple opt-out lists to keep initial scope small.
    muted_modules = models.JSONField(
        default=list, blank=True
    )  # e.g. ["task", "project"]
    muted_action_types = models.JSONField(
        default=list, blank=True
    )  # e.g. ["task_completed"]
    muted_project_ids = models.JSONField(default=list, blank=True)  # e.g. [1, 2, 3]

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
