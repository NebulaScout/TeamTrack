import os
from django.core.management import BaseCommand, call_command
from django.db import IntegrityError, transaction
from django.utils import timezone

from core.models import SeedRun


class Command(BaseCommand):
    help = "Run all seed commands once per database"

    SEED_NAME = "initial_seed_v1"

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                seed_run = SeedRun.objects.create(name=self.SEED_NAME, status="running")
        except IntegrityError:
            self.stdout.write(self.style.WARNING("Seed already ran. Skipping."))
            return

        seed_commands = [
            "init_roles",
            "seed_users",
            "seed_groups",
            "seed_avatars",
            "seed_projects",
            "seed_tasks",
            "seed_calendar",
            "seed_audit_logs",
            "generate_profiles",
        ]

        os.environ["SEED_RUN_NAME"] = self.SEED_NAME

        try:
            for cmd in seed_commands:
                self.stdout.write(self.style.NOTICE(f"Running {cmd}..."))
                call_command(cmd)

            SeedRun.objects.filter(pk=seed_run.pk).update(
                status="success",
                finished_at=timezone.now(),
            )
            self.stdout.write(self.style.SUCCESS("Seeding completed successfully."))
        except Exception:
            SeedRun.objects.filter(pk=seed_run.pk).delete()
            raise
        finally:
            os.environ.pop("SEED_RUN_NAME", None)
