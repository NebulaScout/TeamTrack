from django.core.management.base import BaseCommand
from faker import Faker
from datetime import timedelta, time, datetime
import random
from django.contrib.auth.models import User
from django.utils import timezone

from projects.models import ProjectsModel, ProjectMembers
from tasks.models import TaskModel
from Calendar.models import (
    CalendarEvent,
    ProjectMilestone,
    TaskDeadlineSync,
    CalendarView,
)
from core.services.enums import (
    EventTypesEnum,
    PriorityEnum,
    StatusEnum,
    RecurrenceEnums,
)


class Command(BaseCommand):
    help = "Seed database with fake calendar data"

    def handle(self, *args, **options):
        fake = Faker()

        # Get all projects
        projects = list(ProjectsModel.objects.all())
        if not projects:
            self.stdout.write(
                self.style.ERROR(
                    "No projects in the database. Please run seed_projects first."
                )
            )
            return

        # Get all tasks
        tasks = list(TaskModel.objects.all())
        if not tasks:
            self.stdout.write(
                self.style.WARNING(
                    "No tasks in the database. Calendar will be seeded with limited data. "
                    "Consider running seed_tasks first for better results."
                )
            )

        # Get all users
        all_users = list(User.objects.all())
        if len(all_users) < 2:
            self.stdout.write(
                self.style.ERROR(
                    "Not enough users in the database. Please run seed_users first."
                )
            )
            return

        # Counters
        total_events_created = 0
        total_milestones_created = 0
        total_syncs_created = 0
        total_views_created = 0

        # Create ProjectMilestones
        self.stdout.write(self.style.NOTICE("\n=== Creating Project Milestones ==="))

        milestone_templates = [
            "Project Kickoff",
            "Requirements Finalization",
            "Design Review",
            "Development Phase 1 Complete",
            "Alpha Release",
            "Beta Testing Begin",
            "User Acceptance Testing",
            "Production Deployment",
            "Project Handover",
            "Documentation Complete",
            "Security Audit Complete",
            "Performance Optimization Done",
            "Integration Testing Complete",
            "MVP Launch",
            "Stakeholder Demo",
            "Sprint Review",
            "Architecture Review",
            "Code Freeze",
            "Quality Assurance Sign-off",
            "Go-Live Approval",
        ]

        for project in projects:
            # Create 2-5 milestones per project
            num_milestones = random.randint(2, 5)

            # Get project members for creator selection
            project_members = list(
                ProjectMembers.objects.filter(project=project).select_related(
                    "project_member"
                )
            )

            if not project_members:
                self.stdout.write(
                    self.style.WARNING(
                        f"Skipping project '{project.project_name}' - no members"
                    )
                )
                continue

            member_users = [member.project_member for member in project_members]

            # Generate milestones spread across project timeline
            if project.start_date and project.end_date:
                days_range = (project.end_date - project.start_date).days

                if days_range > num_milestones:
                    # Divide project timeline into chunks for milestones
                    milestone_dates = []
                    chunk_size = days_range // (num_milestones + 1)

                    for i in range(1, num_milestones + 1):
                        milestone_date = project.start_date + timedelta(
                            days=chunk_size * i + random.randint(-5, 5)
                        )
                        # Ensure milestone date is within project bounds
                        if milestone_date > project.end_date:
                            milestone_date = project.end_date - timedelta(
                                days=random.randint(1, 7)
                            )
                        milestone_dates.append(milestone_date)
                else:
                    # For short projects, use random dates
                    milestone_dates = [
                        project.start_date
                        + timedelta(days=random.randint(0, max(1, days_range)))
                        for _ in range(num_milestones)
                    ]

                milestone_dates.sort()
            else:
                # Fallback: future dates
                milestone_dates = [
                    timezone.now().date() + timedelta(days=random.randint(7, 90))
                    for _ in range(num_milestones)
                ]

            # Create milestones
            used_titles = set()
            for i in range(num_milestones):
                # Get unique milestone title
                milestone_title = random.choice(milestone_templates)
                attempt = 0
                while milestone_title in used_titles and attempt < 20:
                    milestone_title = random.choice(milestone_templates)
                    attempt += 1

                used_titles.add(milestone_title)

                creator = random.choice(member_users)
                due_date = milestone_dates[i]

                milestone = ProjectMilestone.objects.create(
                    project=project,
                    title=milestone_title,
                    description=fake.paragraph(nb_sentences=random.randint(2, 4)),
                    due_date=due_date,
                    priority=random.choice(list(PriorityEnum)),
                    status=random.choice(list(StatusEnum)),
                    create_calendar_event=True,  # This auto-creates calendar events
                    created_by=creator,
                )

                total_milestones_created += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  Created milestone: {milestone_title} for {project.project_name}"
                    )
                )

        # Create Standalone Calendar Events
        self.stdout.write(
            self.style.NOTICE("\n=== Creating Standalone Calendar Events ===")
        )

        event_templates = {
            EventTypesEnum.MEETING: [
                "Team Standup",
                "Sprint Planning",
                "Client Presentation",
                "Technical Discussion",
                "Code Review Session",
                "Retrospective Meeting",
                "Architecture Review",
                "Design Sync",
                "Stakeholder Update",
                "One-on-One",
                "Performance Review",
                "Brainstorming Session",
                "Demo Day",
                "Training Session",
                "All-Hands Meeting",
            ],
            EventTypesEnum.TASK: [
                "Code Review",
                "Write Documentation",
                "Refactor Legacy Code",
                "Database Optimization",
                "Security Assessment",
                "Performance Testing",
                "Bug Triage",
                "Deployment Window",
                "Environment Setup",
                "Data Migration",
            ],
            EventTypesEnum.DEADLINE: [
                "Feature Freeze",
                "Submission Deadline",
                "Release Candidate",
                "Final Review Due",
                "Report Submission",
                "Contract Renewal",
                "License Expiry Check",
                "Compliance Audit",
            ],
            EventTypesEnum.REMINDER: [
                "Weekly Report Reminder",
                "Timesheet Submission",
                "Update Dependencies",
                "Backup Verification",
                "Certificate Renewal Check",
                "Security Patch Review",
                "Monthly Team Sync",
            ],
        }

        # Create events for each user
        for user in all_users:
            # Get projects the user is a member of
            user_projects = list(
                ProjectsModel.objects.filter(members__project_member=user)
            )

            # Create 5-15 events per user
            num_events = random.randint(5, 15)

            for _ in range(num_events):
                # Pick event type
                event_type = random.choice(list(EventTypesEnum))

                # Get appropriate title for event type
                event_title = random.choice(event_templates[event_type])

                # Generate event date (spread across past 30 days to future 90 days)
                days_offset = random.randint(-30, 90)
                event_date = timezone.now().date() + timedelta(days=days_offset)

                # Generate realistic times
                start_hour = random.randint(8, 17)  # 8 AM to 5 PM
                start_minute = random.choice([0, 15, 30, 45])
                start_time = time(start_hour, start_minute)

                # Duration: 15 min to 3 hours
                duration_minutes = random.choice([15, 30, 45, 60, 90, 120, 180])
                end_datetime = datetime.combine(
                    datetime.today(), start_time
                ) + timedelta(minutes=duration_minutes)
                end_time = end_datetime.time()

                # Link to project (50% chance if user has projects)
                linked_project = None
                if user_projects and random.random() > 0.5:
                    linked_project = random.choice(user_projects)

                # Recurrence settings
                is_recurring = random.random() > 0.8  # 20% recurring
                recurrence_pattern = None
                if is_recurring:
                    recurrence_pattern = random.choice(list(RecurrenceEnums))

                # Reminder settings
                send_reminder = random.random() > 0.4  # 60% have reminders
                reminder_minutes = (
                    random.choice([15, 30, 60, 120, 1440]) if send_reminder else 30
                )

                event = CalendarEvent.objects.create(
                    user=user,
                    title=event_title,
                    description=fake.paragraph(nb_sentences=random.randint(1, 3)),
                    event_type=event_type,
                    priority=(
                        random.choice(list(PriorityEnum))
                        if random.random() > 0.3
                        else None
                    ),
                    event_date=event_date,
                    start_time=start_time,
                    end_time=end_time,
                    linked_project=linked_project,
                    is_recurring=is_recurring,
                    recurrence_pattern=recurrence_pattern,
                    send_reminder=send_reminder,
                    reminder_minutes_before=reminder_minutes,
                )

                total_events_created += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"  Created {num_events} events for user: {user.username}"
                )
            )

        # Create TaskDeadlineSync records
        self.stdout.write(self.style.NOTICE("\n=== Creating Task Deadline Syncs ==="))

        # Sync 70% of tasks with due dates
        tasks_with_due_dates = [task for task in tasks if task.due_date]

        for task in tasks_with_due_dates:
            if random.random() > 0.3:  # 70% of tasks with due dates
                sync = TaskDeadlineSync.objects.create(
                    task=task, auto_sync_enabled=True
                )
                # Trigger the sync to create calendar events
                sync.sync_to_calendar()
                total_syncs_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"  Created {total_syncs_created} task deadline syncs with calendar events"
            )
        )

        # Create CalendarView preferences for users
        self.stdout.write(
            self.style.NOTICE("\n=== Creating Calendar View Preferences ===")
        )

        default_views = ["DAY", "WEEK", "MONTH", "AGENDA"]

        for user in all_users:
            # Get user's projects
            user_projects = list(
                ProjectsModel.objects.filter(members__project_member=user)
            )

            calendar_view = CalendarView.objects.create(
                user=user,
                default_view=random.choice(default_views),
                show_weekends=random.choice([True, False]),
                show_tasks=random.choice([True, False]),
                show_milestones=random.choice([True, False]),
                show_meetings=random.choice([True, False]),
            )

            # Add filtered projects (show only selected projects - 50% of user's projects)
            if user_projects:
                num_filtered = random.randint(0, max(1, len(user_projects) // 2))
                filtered_projects = random.sample(user_projects, num_filtered)
                calendar_view.filtered_projects.set(filtered_projects)

            total_views_created += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"  Created calendar preferences for: {user.username}"
                )
            )

        # Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("Calendar seeding completed!"))
        self.stdout.write(
            self.style.SUCCESS(
                f"Project Milestones created: {total_milestones_created}"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(f"Calendar Events created: {total_events_created}")
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Task Deadline Syncs created: {total_syncs_created} (with auto calendar events)"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Calendar View Preferences created: {total_views_created}"
            )
        )

        # Count total calendar events (including those auto-created by milestones and syncs)
        total_calendar_events = CalendarEvent.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Total Calendar Events in database: {total_calendar_events}"
            )
        )
        self.stdout.write("=" * 60)
