from django.core.management.base import BaseCommand
from faker import Faker
import random

from django.contrib.auth.models import User
from accounts.models import UserProfile

class Command(BaseCommand):
    help = "Seed the database with fake user data"

    def handle(self, *args, **options):
        fake = Faker()

        # Determine role counts
        roles = {
            'Admin': 3,
            'Project Manager': 5,
            'Developer': 15,
            'Guest': 8
        }

        created_count = 0

        for role, count in roles.items():
            for i in range(count):
                # Create user
                username = fake.user_name()
                email = fake.email()

                # Avoid Duplicates
                while User.objects.filter(username=username).exists():
                    username = fake.user_name()

                while User.objects.filter(email=email).exists():
                    email = fake.email()

                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password='defaultPassword123',
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    is_staff=(role == 'Admin'),
                    is_superuser=(role == 'Admin')
                )

                # Create UserProfile only if it exists
                profile, created = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={'bio': fake.sentence(nb_words=10)}
                )

                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created {role}: {username}'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully created {created_count} users'
            )
        )
