from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

from .models import NotificationPreference
from .services import NotificationService
from audit.models import GlobalAuditLog


@receiver(post_save, sender=User)
def create_notification_preferences(sender, instance, created, **kwargs):
    if created:
        NotificationPreference.objects.get_or_create(user=instance)


@receiver(post_save, sender=GlobalAuditLog)
def emit_notifications_from_audit(sender, instance, created, **kwargs):
    if created:
        NotificationService.create_from_audit(instance)
