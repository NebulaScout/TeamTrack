import os
from django.core.management import BaseCommand, call_command
from django.db import IntegrityError, transaction
from django.utils import timezone

from core.models import SeedRun


class Command(BaseCommand):
    help = "Run all seed commands once per database"

    SEED_NAME = "initial_seed_v1"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Allow rerunning by creating a new seed run record.",
        )
        parser.add_argument(
            "--run-id",
            dest="run_id",
            help="Optional seed run name override.",
        )

    def handle(self, *args, **options):
        run_id = options.get("run_id") or os.getenv("SEED_RUN_NAME")
        seed_name = run_id or self.SEED_NAME

        try:
            with transaction.atomic():
                seed_run = SeedRun.objects.create(name=seed_name, status="running")
        except IntegrityError:
            if not options.get("force"):
                self.stdout.write(self.style.WARNING("Seed already ran. Skipping."))
                return

            # Create a unique run name for reruns.
            suffix = timezone.now().strftime("%Y%m%d%H%M%S")
            seed_name = f"{seed_name}_{suffix}"
            with transaction.atomic():
                seed_run = SeedRun.objects.create(name=seed_name, status="running")

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

        os.environ["SEED_RUN_NAME"] = seed_name

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
