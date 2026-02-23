from django.core.management.base import BaseCommand
from faker import Faker
from datetime import timedelta
import random

from django.contrib.auth.models import User, Group
from projects.models import ProjectsModel, ProjectMembers
from core.services.roles import ROLE_PERMISSIONS


class Command(BaseCommand):
    help = "Seed database with fake project data"

    def handle(self, *args, **options):
        fake = Faker()

        # Get all users to assign as creators and members
        users = list(User.objects.all())

        if len(users) < 3:
            self.stdout.write(
                self.style.ERROR(
                    "Not enough users in the database. Please run seed_user first."
                )
            )
            return

        # Project categories for realistic names
        project_prefixes = [
            "E-Commerce",
            "Healthcare",
            "Finance",
            "Education",
            "Social Media",
            "Analytics",
            "CRM",
            "Inventory",
            "HR Management",
            "Supply Chain",
            "Marketing",
            "IoT",
            "Real Estate",
            "Logistics",
            "Cybersecurity",
            "Travel",
            "Food Delivery",
            "Legal",
            "Insurance",
            "Retail",
            "Telemedicine",
            "EdTech",
            "FinTech",
            "Blockchain",
            "AI-Powered",
            "Cloud",
            "Automotive",
            "Media Streaming",
            "Event Management",
            "Construction",
            "Agriculture",
            "Gaming",
        ]

        project_suffixes = [
            "Platform",
            "System",
            "Application",
            "Portal",
            "Dashboard",
            "API",
            "Service",
            "Module",
            "Engine",
            "Hub",
            "Suite",
            "Gateway",
            "Tracker",
            "Manager",
            "Network",
            "Framework",
            "Tool",
            "Workspace",
            "Interface",
            "Solution",
        ]

        num_projects = 25
        created_count = 0

        for i in range(num_projects):
            # Generate unique project names
            project_name = (
                f"{random.choice(project_prefixes)} {random.choice(project_suffixes)}"
            )

            # Avoid duplicates
            while ProjectsModel.objects.filter(project_name=project_name).exists():
                project_name = f"{random.choice(project_prefixes)} {random.choice(project_suffixes)}"

            # Generate dates
            start_date = fake.date_between(start_date="-1y", end_date="today")
            end_date = start_date + timedelta(days=random.randint(30, 365))

            # Get users who belong to Admin or Project Manager Groups
            admin_group = Group.objects.filter(name="Admin").first()
            pm_group = Group.objects.filter(name="Project Manager").first()

            eligible_creators = User.objects.filter(
                groups__in=[g for g in [admin_group, pm_group] if g]
            ).distinct()

            creator = (
                random.choice(list(eligible_creators))
                if eligible_creators.exists()
                else random.choice(users)
            )

            project = ProjectsModel.objects.create(
                project_name=project_name,
                description=fake.paragraph(nb_sentences=5),
                start_date=start_date,
                end_date=end_date,
                created_by=creator,
            )

            created_count += 1
            self.stdout.write(self.style.SUCCESS(f"Created project: {project_name}"))

            # Add project members (3-8 members per project)
            num_members = random.randint(3, min(8, len(users)))
            available_users = [u for u in users if u != creator]
            selected_members = random.sample(
                available_users, min(num_members, len(available_users))
            )

            # Available roles from ROLE_PERMISSIONS
            roles = list(ROLE_PERMISSIONS.keys())

            # Always add the creator as Admin
            ProjectMembers.objects.get_or_create(
                project=project,
                project_member=creator,
                defaults={"role_in_project": "Admin"},
            )

            # Add other members with various roles
            for member in selected_members:
                # Weight roles more developers, fewer Admins
                role_weights = {
                    "Admin": 1,
                    "Project Manager": 2,
                    "Developer": 5,
                    "Guest": 2,
                }

                weighted_roles = []
                for role in roles:
                    weighted_roles.extend([role] * role_weights.get(role, 1))

                role = random.choice(weighted_roles)

                ProjectMembers.objects.get_or_create(
                    project=project,
                    project_member=member,
                    defaults={"role_in_project": role},
                )

                self.stdout.write(
                    self.style.NOTICE(f"  Added member: {member.username} as {role}")
                )

            self.stdout.write(
                self.style.SUCCESS(f"\nSuccessfully created {created_count} projects")
            )
