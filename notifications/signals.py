from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db import transaction

from .models import NotificationPreference, Notification
from .services import NotificationService
from audit.models import GlobalAuditLog


@receiver(post_save, sender=User, dispatch_uid="notifications_create_pref")
def create_notification_preferences(sender, instance, created, **kwargs):
    if created:
        NotificationPreference.objects.get_or_create(user=instance)


@receiver(
    post_save, sender=GlobalAuditLog, dispatch_uid="notifications_emit_from_audit"
)
def emit_notifications_from_audit(sender, instance, created, **kwargs):
    if not created:
        return

    def _create():
        if Notification.objects.filter(audit_log=instance).exists():
            return
        NotificationService.create_from_audit(instance)

    transaction.on_commit(_create)
