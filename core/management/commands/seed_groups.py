from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
import random


class Command(BaseCommand):
    help = "Seed groups and assign existing users to groups"

    def handle(self, *args, **options):
        # Define the groups to create
        group_names = ["Admin", "Project Manager", "Developer", "Guest"]

        # Create groups if they don't exist
        for name in group_names:
            group, created = Group.objects.get_or_create(name=name)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created group: {name}"))
            else:
                self.stdout.write(self.style.NOTICE(f"Groups already exists: {name}"))

        # Get all users without a group
        users_without_group = User.objects.filter(groups__isnull=True)

        if not users_without_group.exists():
            self.stdout.write(
                self.style.WARNING("All users already have groups assigned.")
            )
            return

        self.stdout.write(
            self.style.NOTICE(
                f"\nAssigning groups to {users_without_group.count()} users..."
            )
        )

        # Get group objects
        admin_group = Group.objects.get(name="Admin")
        pm_group = Group.objects.get(name="Project Manager")
        dev_group = Group.objects.get(name="Developer")
        guest_group = Group.objects.get(name="Guest")

        assigned_counts = {
            "Admin": 0,
            "Project Manager": 0,
            "Developer": 0,
            "Guest": 0,
        }

        for user in users_without_group:
            # Determine group based on user attributes
            if user.is_superuser or user.is_staff:
                # superusers and staff are admins
                user.groups.add(admin_group)
                assigned_counts["Admin"] += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Assigned {user.username} -> Admin")
                )

            else:
                # Distribute other users with weighted random selection
                # more developers, less project managers
                weighted_choices = (
                    [pm_group] * 2  # 20% PMs
                    + [dev_group] * 5  # 50% Devs
                    + [guest_group] * 3  # 30% Guests
                )

                selected_group = random.choice(weighted_choices)
                user.groups.add(selected_group)
                assigned_counts[selected_group.name] += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Assigned {user.username} -> {selected_group.name}"
                    )
                )

        self.stdout.write("\n" + "=" * 40)
        self.stdout.write(self.style.SUCCESS("Assignment Summary:"))
        for group_name, count in assigned_counts.items():
            self.stdout.write(f"  {group_name}: {count} users")

        self.stdout.write(
            self.style.SUCCESS(
                f"\nTotal users assigned: {sum(assigned_counts.values())}"
            )
        )
