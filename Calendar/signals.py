from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from tasks.models import TaskModel
from .models import TaskDeadlineSync, CalendarEvent


@receiver(post_save, sender=TaskModel)
def auto_sync_task_deadline(sender, instance, created, **kwargs):
    """Automatically create calendar events when task due date changes"""
    if instance.due_date and instance.assigned_to:
        # get or create sync object
        sync, _ = TaskDeadlineSync.objects.get_or_create(
            task=instance, defaults={"auto_sync_enabled": True}
        )

        # sync to calendar if enabled
        if sync.auto_sync_enabled:
            sync.sync_to_calendar()


@receiver(pre_delete, sender=TaskModel)
def cleanup_task_calendar_events(sender, instance, **kwargs):
    """Clean up calendar events when a task is deleted"""
    CalendarEvent.objects.filter(linked_task=instance).delete()
