from django.apps import AppConfig


class CalendarConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "Calendar"

    def ready(self):
        import Calendar.signals  # noqa
