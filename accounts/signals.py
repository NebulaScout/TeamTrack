from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """On user register, create the profile"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(m2m_changed, sender=User.groups.through)
def sync_staff_from_admin_group(sender, instance, action, **kwargs):
    if action not in {"post_add", "post_remove", "post_clear"}:
        return

    should_be_staff = (
        instance.is_superuser or instance.groups.filter(name="Admin").exists()
    )
    if instance.is_staff != should_be_staff:
        User.objects.filter(pk=instance.pk).update(is_staff=should_be_staff)
