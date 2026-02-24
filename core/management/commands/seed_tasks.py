from django.core.management.base import BaseCommand
from faker import Faker
from datetime import timedelta
import random
from django.contrib.auth.models import User
from django.utils import timezone

from projects.models import ProjectsModel, ProjectMembers
from tasks.models import TaskModel, CommentModel, TaskHistoryModel, TaskAssignment
from core.services.enums import StatusEnum, PriorityEnum, TaskFieldEnum


class Command(BaseCommand):
    help = "Seed database with fake task data"

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

        # Get all users as fallback
        all_users = list(User.objects.all())

        if len(all_users) < 2:
            self.stdout.write(
                self.style.ERROR(
                    "Not enough users in the database. Please run seed_users and seed_avatars in that order."
                )
            )
            return

        # Task title prefixes and suffixes for realistic names
        task_prefixes = [
            "Implement",
            "Fix",
            "Update",
            "Create",
            "Design",
            "Review",
            "Test",
            "Refactor",
            "Optimize",
            "Document",
            "Configure",
            "Deploy",
            "Integrate",
            "Migrate",
            "Debug",
            "Build",
            "Set up",
            "Analyze",
            "Research",
            "Plan",
        ]

        task_subjects = [
            "user authentication",
            "payment gateway",
            "dashboard UI",
            "API endpoints",
            "database schema",
            "email notifications",
            "search functionality",
            "file upload feature",
            "user profile page",
            "admin panel",
            "reporting module",
            "caching layer",
            "error handling",
            "unit tests",
            "CI/CD pipeline",
            "security audit",
            "performance metrics",
            "mobile responsiveness",
            "data validation",
            "logging system",
            "backup system",
            "user permissions",
            "third-party integration",
            "export functionality",
            "import functionality",
            "notification system",
            "comment feature",
            "audit trail",
            "dark mode toggle",
            "localization support",
        ]

        # Sample comments for realism
        comment_templates = [
            "I've started working on this. Should be done by {date}.",
            "Found an issue with the current implementation. Investigating further.",
            "This is blocked by the {blocker} task. Can we prioritize that first?",
            "Completed the initial implementation. Ready for review.",
            "Added some unit tests for this feature.",
            "Can someone clarify the requirements for this?",
            "Updated the documentation for this change.",
            "This might need more time than estimated.",
            "Great progress on this! Just a few tweaks needed.",
            "Pushed the latest changes. Please review when you get a chance.",
            "Had to refactor some related code. All tests passing now.",
            "This is ready for QA testing.",
            "Found a bug during testing. Working on a fix.",
            "Merged the PR. Deploying to staging.",
            "Successfully deployed. Monitoring for any issues.",
            # Progress updates
            "Left some inline comments on the PR. Please address before merging.",
            "Still in progress — ran into an unexpected edge case.",
            "Picking this up after the weekend. Will update by EOD Monday.",
            "Almost done, just need to handle the error cases.",
            "Pausing this for now due to higher priority tasks.",
            # Collaboration & communication
            # "Assigned this to {assignee} — better suited for their expertise.",
            "Discussed with the team. We agreed to go with approach B.",
            "Waiting on feedback from the client before proceeding.",
            # "Pinged {assignee} on Slack for clarification.",
            "Scheduled a quick sync to discuss the implementation details.",
            # Code quality & review
            "Refactored to improve readability. Logic remains the same.",
            "Removed dead code and cleaned up unused imports.",
            "Added error handling for the edge cases we missed earlier.",
            "Code review done. Left a few minor suggestions.",
            "Addressed all review comments. Ready for a second look.",
            # Testing & QA
            "All existing tests pass. Added 3 new test cases.",
            "Reproduced the bug locally. Fix incoming.",
            "QA approved. Ready to merge into main.",
            "Regression tests passed successfully.",
            "Noticed a performance issue under load. Needs optimization.",
            # Deployment & ops
            "Rolled back the last deployment due to an unexpected error.",
            "Hotfix applied to production. Monitoring closely.",
            "Environment variables updated on the staging server.",
            "Database migration ran successfully.",
            "Added feature flag for a safer rollout.",
            # Estimation & planning
            # "Re-estimated: this will take {days} more days than expected.",
            "Breaking this into smaller subtasks for better tracking.",
            "Complexity is higher than anticipated. Updating the estimate.",
            "This turned out simpler than expected. Finished ahead of schedule.",
        ]

        statuses = list(StatusEnum)
        priorities = list(PriorityEnum)

        total_tasks_created = 0
        total_comments_created = 0
        total_history_created = 0
        total_assignment_created = 0

        for project in projects:
            # Get project members
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

            # Extract users from project members
            member_users = [member.project_member for member in project_members]

            # Determine number of tasks per project (5-15)
            num_tasks = random.randint(5, 15)

            self.stdout.write(
                self.style.NOTICE(
                    f"\nCreating {num_tasks} tasks for project: {project.project_name}"
                )
            )

            for _ in range(num_tasks):
                # Generate unique task title
                task_title = (
                    f"{random.choice(task_prefixes)} {random.choice(task_subjects)}"
                )

                # Ensure some uniquesness within the project
                attempt = 0
                while (
                    TaskModel.objects.filter(project=project, title=task_title).exists()
                    and attempt < 10
                ):
                    task_title = (
                        f"{random.choice(task_prefixes)} {random.choice(task_subjects)}"
                    )
                    attempt += 1

                # Calculate due date within project timeline
                if project.start_date and project.end_date:
                    # Due date should be between project start and end date
                    days_range = (project.end_date - project.start_date).days
                    if days_range > 0:
                        due_date = project.start_date + timedelta(
                            days=random.randint(1, days_range)
                        )
                    else:
                        due_date = project.end_date
                else:
                    # Fallback due date within the next 30-90 days
                    due_date = timezone.now().date() + timedelta(
                        days=random.randint(30, 90)
                    )

                # Selet creator(prefer Admin or Project Manager)
                creator = random.choice(member_users)

                # Select assignee (can be none sometimes)
                assigned_to = None
                if random.random() > 0.1:  # 90% chance of assigment
                    assigned_to = random.choice(member_users)

                # create the task
                task = TaskModel.objects.create(
                    project=project,
                    title=task_title,
                    description=fake.paragraph(nb_sentences=random.randint(2, 6)),
                    assigned_to=assigned_to,
                    status=random.choice(statuses),
                    priority=random.choice(priorities),
                    due_date=due_date,
                    created_by=creator,
                )

                total_tasks_created += 1
                self.stdout.write(self.style.SUCCESS(f"\tCreated task: {task_title}"))

                # Create TaskAssignment records (can have multiple assignees)
                if assigned_to:
                    TaskAssignment.objects.get_or_create(
                        task=task,
                        user=assigned_to,
                    )
                    total_assignment_created += 1

                    # Sometimes add additional assignees (for collaborative tasks)
                    if random.random() > 0.7 and len(member_users) > 1:
                        additional_assignees = random.sample(
                            [user for user in member_users if user != assigned_to],
                            min(random.randint(1, 2), len(member_users) - 1),
                        )

                        for extra_user in additional_assignees:
                            TaskAssignment.objects.get_or_create(
                                task=task,
                                user=extra_user,
                            )
                            total_assignment_created += 1

                # Create comments (0 - 9 per task)
                num_comments = random.randint(0, 9)
                for _ in range(num_comments):
                    comment_content = random.choice(comment_templates).format(
                        date=fake.date_between(start_date="today", end_date="+30d"),
                        blocker=random.choice(task_subjects),
                    )

                    CommentModel.objects.create(
                        task=task,
                        author=random.choice(member_users),
                        content=comment_content,
                    )
                    total_comments_created += 1

                    # create task history (0 - 4 entries per task to simulate changes)
                    num_history = random.randint(0, 4)

                    # fields that can be tracked in history
                    trackable_fields = [
                        TaskFieldEnum.STATUS,
                        TaskFieldEnum.PRIORITY,
                        TaskFieldEnum.ASSIGNED_TO,
                        TaskFieldEnum.DUE_DATE,
                    ]

                    for _ in range(num_history):
                        field_changed = random.choice(trackable_fields)
                        changed_by = random.choice(member_users)

                        # Generate realistic old and new values based on field type
                        if field_changed == TaskFieldEnum.STATUS:
                            old_status, new_status = random.sample(list(StatusEnum), 2)
                            old_value = old_status.value
                            new_value = new_status.value
                        elif field_changed == TaskFieldEnum.PRIORITY:
                            old_priority, new_priority = random.sample(
                                list(PriorityEnum), 2
                            )
                            old_value = old_priority.value
                            new_value = new_priority.value
                        elif field_changed == TaskFieldEnum.ASSIGNED_TO:
                            if len(member_users) > 2:
                                old_user, new_user = random.sample(
                                    list(member_users), 2
                                )
                                old_value = old_user.username
                                new_value = new_user.username
                            else:
                                old_value = None
                                new_value = member_users[0].username
                        elif field_changed == TaskFieldEnum.DUE_DATE:
                            old_value = str(
                                fake.date_between(start_date="-30d", end_date="today")
                            )
                            new_value = str(
                                fake.date_between(start_date="today", end_date="+60d")
                            )
                        else:
                            old_value = fake.sentence()
                            new_value = fake.sentence()

                        TaskHistoryModel.objects.create(
                            task=task,
                            changed_by=changed_by,
                            field_changed=field_changed,
                            old_value=old_value,
                            new_value=new_value,
                            timestamp=fake.date_time_between(
                                start_date="-30d",
                                end_date="now",
                                tzinfo=timezone.get_current_timezone(),
                            ),
                        )
                        total_history_created += 1

        # summary
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS(f"Seeding completed!"))
        self.stdout.write(self.style.SUCCESS(f"Tasks created: {total_tasks_created}"))
        self.stdout.write(
            self.style.SUCCESS(f"Comments created: {total_comments_created}")
        )
        self.stdout.write(
            self.style.SUCCESS(f"History entries created: {total_history_created}")
        )
        self.stdout.write(
            self.style.SUCCESS(f"Task assginments created: {total_assignment_created}")
        )
