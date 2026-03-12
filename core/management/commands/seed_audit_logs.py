from django.core.management.base import BaseCommand
from faker import Faker
from datetime import timedelta
import random
from django.contrib.auth.models import User
from django.utils import timezone

from projects.models import ProjectsModel, ProjectMembers
from tasks.models import TaskModel, TaskHistoryModel
from core.services.enums import (
    StatusEnum,
    PriorityEnum,
    TaskFieldEnum,
)


class Command(BaseCommand):
    help = "Seed database with comprehensive audit log data for admin dashboard"

    def add_arguments(self, parser):
        parser.add_argument(
            "--entries",
            type=int,
            default=200,
            help="Approximate number of audit log entries to create (default: 200)",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=60,
            help="Number of days in the past to spread logs across (default: 60)",
        )

    def handle(self, *args, **options):
        fake = Faker()
        target_entries = options["entries"]
        days_back = options["days"]

        # Get all tasks
        tasks = list(TaskModel.objects.select_related("project", "created_by").all())
        if not tasks:
            self.stdout.write(
                self.style.ERROR(
                    "No tasks in the database. Please run seed_tasks first."
                )
            )
            return

        # Get all users
        all_users = list(User.objects.all())
        if len(all_users) < 2:
            self.stdout.write(
                self.style.ERROR(
                    "Not enough users in the database. Please run seed_users first."
                )
            )
            return

        self.stdout.write(
            self.style.NOTICE(
                f"\n=== Seeding {target_entries} audit log entries across {days_back} days ==="
            )
        )

        total_logs_created = 0

        # Field distribution - weight certain fields to appear more often
        field_weights = {
            TaskFieldEnum.STATUS: 35,  # Status changes are most common
            TaskFieldEnum.PRIORITY: 20,  # Priority changes fairly common
            TaskFieldEnum.ASSIGNED_TO: 25,  # Assignments/reassignments common
            TaskFieldEnum.DUE_DATE: 10,  # Due date changes moderately common
            TaskFieldEnum.TITLE: 6,  # Title changes less common
            TaskFieldEnum.DESCRIPTION: 4,  # Description changes least common
        }

        weighted_fields = []
        for field, weight in field_weights.items():
            weighted_fields.extend([field] * weight)

        # Create audit logs
        for _ in range(target_entries):
            task = random.choice(tasks)
            field_changed = random.choice(weighted_fields)

            # Get project members for this task's project as potential change makers
            if task.project:
                project_members = list(
                    ProjectMembers.objects.filter(project=task.project).select_related(
                        "project_member"
                    )
                )

                if project_members:
                    member_users = [member.project_member for member in project_members]
                    changed_by = random.choice(member_users)
                else:
                    changed_by = task.created_by or random.choice(all_users)
            else:
                changed_by = task.created_by or random.choice(all_users)

            # Generate realistic old and new values based on field type
            old_value = None
            new_value = None

            if field_changed == TaskFieldEnum.STATUS:
                # Create realistic status progression
                status_progressions = [
                    (StatusEnum.TO_DO, StatusEnum.IN_PROGRESS),
                    (StatusEnum.IN_PROGRESS, StatusEnum.IN_REVIEW),
                    (StatusEnum.IN_REVIEW, StatusEnum.DONE),
                    (StatusEnum.IN_REVIEW, StatusEnum.IN_PROGRESS),  # Sent back
                    (StatusEnum.TO_DO, StatusEnum.IN_REVIEW),  # Fast-tracked
                    (StatusEnum.IN_PROGRESS, StatusEnum.TO_DO),  # Blocked/paused
                    (StatusEnum.DONE, StatusEnum.IN_PROGRESS),  # Reopened
                ]
                old_status, new_status = random.choice(status_progressions)
                old_value = old_status.value
                new_value = new_status.value

            elif field_changed == TaskFieldEnum.PRIORITY:
                # Priority escalations and de-escalations
                priorities = list(PriorityEnum)
                old_priority, new_priority = random.sample(priorities, 2)
                old_value = old_priority.value
                new_value = new_priority.value

            elif field_changed == TaskFieldEnum.ASSIGNED_TO:
                # Assignment changes
                if task.project:
                    project_members = list(
                        ProjectMembers.objects.filter(
                            project=task.project
                        ).select_related("project_member")
                    )

                    if len(project_members) >= 2:
                        member_users = [
                            member.project_member for member in project_members
                        ]
                        old_user, new_user = random.sample(member_users, 2)
                        old_value = old_user.username
                        new_value = new_user.username
                    elif len(project_members) == 1:
                        # Assigned to someone from unassigned
                        old_value = "Unassigned"
                        new_value = project_members[0].project_member.username
                    else:
                        old_value = None
                        new_value = random.choice(all_users).username
                else:
                    if len(all_users) >= 2:
                        old_user, new_user = random.sample(all_users, 2)
                        old_value = old_user.username
                        new_value = new_user.username
                    else:
                        old_value = "Unassigned"
                        new_value = all_users[0].username

            elif field_changed == TaskFieldEnum.DUE_DATE:
                # Due date changes - pushed back or brought forward
                days_shift = random.choice([-14, -7, -3, 3, 7, 14, 21])  # Common shifts
                old_date = fake.date_between(start_date="-30d", end_date="+30d")
                new_date = old_date + timedelta(days=days_shift)
                old_value = str(old_date)
                new_value = str(new_date)

            elif field_changed == TaskFieldEnum.TITLE:
                # Title refinements or corrections
                title_changes = [
                    ("Implement feature X", "Implement user authentication feature"),
                    ("Fix bug", "Fix login redirect bug"),
                    ("Update UI", "Update dashboard UI components"),
                    ("Test endpoint", "Test payment API endpoint"),
                    ("Create documentation", "Create API documentation"),
                    ("Setup database", "Setup PostgreSQL database"),
                    ("Refactor code", "Refactor authentication service"),
                    ("Add validation", "Add form input validation"),
                    ("Optimize query", "Optimize user search query"),
                    ("Deploy changes", "Deploy to production environment"),
                ]
                old_value, new_value = random.choice(title_changes)

            elif field_changed == TaskFieldEnum.DESCRIPTION:
                # Description updates - more details added
                old_value = fake.sentence(nb_words=10)
                new_value = fake.paragraph(nb_sentences=3)

            # Generate timestamp spread across the specified days
            timestamp = fake.date_time_between(
                start_date=f"-{days_back}d",
                end_date="now",
                tzinfo=timezone.get_current_timezone(),
            )

            # Create the audit log entry
            try:
                TaskHistoryModel.objects.create(
                    task=task,
                    changed_by=changed_by,
                    field_changed=field_changed,
                    old_value=old_value,
                    new_value=new_value,
                    timestamp=timestamp,
                )
                total_logs_created += 1

                # Progress indicator every 50 entries
                if total_logs_created % 50 == 0:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  Created {total_logs_created} audit log entries..."
                        )
                    )

            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"  Failed to create log entry: {str(e)}")
                )
                continue

        # Create some focused activity patterns for realism
        self.stdout.write(
            self.style.NOTICE("\n=== Creating focused activity patterns ===")
        )

        # Pattern 1: Task lifecycle (creation to completion)
        lifecycle_tasks = random.sample(tasks, min(10, len(tasks)))
        for task in lifecycle_tasks:
            if not task.project:
                continue

            project_members = list(
                ProjectMembers.objects.filter(project=task.project).select_related(
                    "project_member"
                )
            )

            if not project_members:
                continue

            member_users = [member.project_member for member in project_members]

            # Simulate realistic task progression
            base_time = fake.date_time_between(
                start_date=f"-{days_back}d",
                end_date="-7d",
                tzinfo=timezone.get_current_timezone(),
            )

            lifecycle_events = [
                {
                    "field": TaskFieldEnum.STATUS,
                    "old": None,
                    "new": StatusEnum.TO_DO.value,
                    "offset": 0,
                },
                {
                    "field": TaskFieldEnum.ASSIGNED_TO,
                    "old": "Unassigned",
                    "new": random.choice(member_users).username,
                    "offset": random.randint(1, 60),  # minutes
                },
                {
                    "field": TaskFieldEnum.PRIORITY,
                    "old": PriorityEnum.MEDIUM.value,
                    "new": PriorityEnum.HIGH.value,
                    "offset": random.randint(120, 360),  # hours
                },
                {
                    "field": TaskFieldEnum.STATUS,
                    "old": StatusEnum.TO_DO.value,
                    "new": StatusEnum.IN_PROGRESS.value,
                    "offset": random.randint(720, 1440),  # 1-2 days
                },
                {
                    "field": TaskFieldEnum.STATUS,
                    "old": StatusEnum.IN_PROGRESS.value,
                    "new": StatusEnum.IN_REVIEW.value,
                    "offset": random.randint(2880, 5760),  # 2-4 days
                },
                {
                    "field": TaskFieldEnum.STATUS,
                    "old": StatusEnum.IN_REVIEW.value,
                    "new": StatusEnum.DONE.value,
                    "offset": random.randint(7200, 8640),  # 5-6 days
                },
            ]

            for event in lifecycle_events:
                timestamp = base_time + timedelta(minutes=event["offset"])

                try:
                    TaskHistoryModel.objects.create(
                        task=task,
                        changed_by=random.choice(member_users),
                        field_changed=event["field"],
                        old_value=event["old"],
                        new_value=event["new"],
                        timestamp=timestamp,
                    )
                    total_logs_created += 1
                except Exception:
                    continue

        # Pattern 2: Busy days with lots of activity
        num_busy_days = random.randint(3, 5)
        for _ in range(num_busy_days):
            busy_date = fake.date_time_between(
                start_date=f"-{days_back}d",
                end_date="-1d",
                tzinfo=timezone.get_current_timezone(),
            )

            # Create 15-25 log entries for this busy day
            num_entries = random.randint(15, 25)
            for _ in range(num_entries):
                task = random.choice(tasks)
                if not task.project:
                    continue

                project_members = list(
                    ProjectMembers.objects.filter(project=task.project).select_related(
                        "project_member"
                    )
                )

                if not project_members:
                    continue

                member_users = [member.project_member for member in project_members]

                # Random time during the busy day
                timestamp = busy_date + timedelta(
                    hours=random.randint(8, 18), minutes=random.randint(0, 59)
                )

                field_changed = random.choice(
                    [
                        TaskFieldEnum.STATUS,
                        TaskFieldEnum.PRIORITY,
                        TaskFieldEnum.ASSIGNED_TO,
                    ]
                )

                if field_changed == TaskFieldEnum.STATUS:
                    old_status, new_status = random.sample(list(StatusEnum), 2)
                    old_value = old_status.value
                    new_value = new_status.value
                elif field_changed == TaskFieldEnum.PRIORITY:
                    old_priority, new_priority = random.sample(list(PriorityEnum), 2)
                    old_value = old_priority.value
                    new_value = new_priority.value
                else:  # ASSIGNED_TO
                    if len(member_users) >= 2:
                        old_user, new_user = random.sample(member_users, 2)
                        old_value = old_user.username
                        new_value = new_user.username
                    else:
                        continue

                try:
                    TaskHistoryModel.objects.create(
                        task=task,
                        changed_by=random.choice(member_users),
                        field_changed=field_changed,
                        old_value=old_value,
                        new_value=new_value,
                        timestamp=timestamp,
                    )
                    total_logs_created += 1
                except Exception:
                    continue

        # Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("Audit log seeding completed!"))
        self.stdout.write(
            self.style.SUCCESS(f"Total audit log entries created: {total_logs_created}")
        )

        # Show distribution by field type
        field_distribution = {}
        for field in TaskFieldEnum:
            count = TaskHistoryModel.objects.filter(field_changed=field).count()
            field_distribution[field.label] = count

        self.stdout.write(self.style.NOTICE("\nAudit log distribution by field:"))
        for field_name, count in sorted(
            field_distribution.items(), key=lambda x: x[1], reverse=True
        ):
            self.stdout.write(f"  {field_name}: {count} entries")

        # Show recent activity
        recent_logs = TaskHistoryModel.objects.select_related(
            "task", "changed_by"
        ).order_by("-timestamp")[:5]

        if recent_logs:
            self.stdout.write(self.style.NOTICE("\nMost recent audit log entries:"))
            for log in recent_logs:
                task_title = log.task.title if log.task else "Deleted Task"
                user = log.changed_by.username if log.changed_by else "Unknown User"
                self.stdout.write(
                    f"  {log.timestamp.strftime('%Y-%m-%d %H:%M')} - "
                    f"{user} changed {log.field_changed} of '{task_title}'"
                )

        self.stdout.write("=" * 60)
