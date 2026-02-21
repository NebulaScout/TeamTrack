from django.core.management.base import BaseCommand

from django.contrib.auth.models import User
from accounts.models import UserProfile

class Command(BaseCommand):
    help = "Generate missing UserProfile objects for exisitng users"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Checking for users without profiles..."))

        created_count = 0

        for user in User.objects.all():
            profile, created = UserProfile.objects.get_or_create(user=user)

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Created profile for {user.username}")

                )

        self.stdout.write(
            self.style.SUCCESS(f"\nFinished. Profiles created: {created_count}")
        )
