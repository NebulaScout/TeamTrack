from django.db import migrations


def create_prefs(apps, schema_editor):
    User = apps.get_model("auth", "User")
    NotificationPreference = apps.get_model("notifications", "NotificationPreference")

    for user in User.objects.all():
        NotificationPreference.objects.get_or_create(user=user)


class Migration(migrations.Migration):
    dependencies = [
        ("notifications", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_prefs, migrations.RunPython.noop),
    ]
