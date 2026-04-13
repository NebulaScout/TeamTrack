from django.db import models
from collections import defaultdict
from datetime import timedelta
import random

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from faker import Faker

from audit.models import GlobalAuditLog
from core.services.audit_service import AuditService
from core.services.enums import (
    AuditModule,
    PriorityEnum,
    StatusEnum,
    TaskFieldEnum,
)
from projects.models import ProjectMembers, ProjectsModel
from tasks.models import CommentModel, TaskHistoryModel, TaskModel


class Command(BaseCommand):
    help = "Seed realistic TaskHistory + GlobalAuditLog entries aligned with audit relationships"

    def add_arguments(self, parser):
        parser.add_argument(
            "--entries",
            type=int,
            default=300,
            help="Approximate number of GlobalAuditLog entries to create",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=90,
            help="How many days back to spread activity",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing TaskHistoryModel + GlobalAuditLog before seeding",
        )

    def handle(self, *args, **options):
        fake = Faker()
        target_entries = max(1, options["entries"])
        days_back = max(1, options["days"])
        clear_existing = options["clear"]

        users = list(User.objects.all())
        projects = list(ProjectsModel.objects.select_related("created_by").all())
        tasks = list(
            TaskModel.objects.select_related(
                "project",
                "created_by",
                "assigned_to",
            ).all()
        )
        comments = list(
            CommentModel.objects.select_related(
                "task",
                "task__project",
                "author",
            ).all()
        )

        if len(users) < 2:
            self.stdout.write(
                self.style.ERROR("Not enough users. Run seed_users first.")
            )
            return

        if not projects:
            self.stdout.write(
                self.style.ERROR("No projects found. Run seed_projects first.")
            )
            return

        if not tasks:
            self.stdout.write(self.style.ERROR("No tasks found. Run seed_tasks first."))
            return

        project_ids = [p.pk for p in projects]
        memberships = list(
            ProjectMembers.objects.filter(project_id__in=project_ids).select_related(
                "project_member",
                "project",
            )
        )

        members_by_project = defaultdict(list)
        for m in memberships:
            members_by_project[m.project.pk].append(m.project_member)

        # Guarantee at least one actor for each project.
        for p in projects:
            if not members_by_project[p.pk]:
                if p.created_by:
                    members_by_project[p.pk].append(p.created_by)
                else:
                    members_by_project[p.pk].append(random.choice(users))

        if clear_existing:
            self.stdout.write(
                self.style.WARNING("Clearing existing audit/task history logs...")
            )
            GlobalAuditLog.objects.all().delete()
            TaskHistoryModel.objects.all().delete()

        # Keep mutable in-memory state so old/new values are coherent across events.
        task_state = {}
        for t in tasks:
            task_state[t.pk] = {
                "status": str(t.status) if t.status else "",
                "priority": str(t.priority) if t.priority else "",
                "assigned_to": t.assigned_to.username if t.assigned_to else "",
                "due_date": str(t.due_date) if t.due_date else "",
                "title": t.title or "",
                "description": t.description or "",
            }

        created = {
            "global_logs": 0,
            "task_history": 0,
            "task_updates": 0,
            "task_created": 0,
            "task_deleted": 0,
            "comment_created": 0,
            "project_updated": 0,
            "user_registered": 0,
        }

        self.stdout.write(
            self.style.NOTICE(
                f"Seeding about {target_entries} audit events over the last {days_back} days..."
            )
        )

        event_types = [
            "task_update",
            "task_create",
            "task_delete",
            "comment_create",
            "project_update",
            "user_registered",
        ]
        # Weight heavily toward task updates because they also drive TaskHistory.
        event_weights = [58, 10, 5, 14, 8, 5]

        with transaction.atomic():
            for idx in range(target_entries):
                event = random.choices(event_types, weights=event_weights, k=1)[0]
                occurred_at = fake.date_time_between(
                    start_date=f"-{days_back}d",
                    end_date="now",
                    tzinfo=timezone.get_current_timezone(),
                )

                if event == "task_update":
                    ok = self._create_task_update(
                        task=random.choice(tasks),
                        state=task_state,
                        users=users,
                        members_by_project=members_by_project,
                        occurred_at=occurred_at,
                    )
                    if ok:
                        created["task_updates"] += 1
                        created["global_logs"] += 1
                        created["task_history"] += 1

                elif event == "task_create":
                    task = random.choice(tasks)
                    actor = self._pick_actor(task.project.pk, members_by_project, users)
                    AuditService.created(
                        module=AuditModule.TASK,
                        actor=actor,
                        target=task,
                        project=task.project,
                        description=f'Created task "{task.title}"',
                        metadata={
                            "task_title": task.title,
                            "status": str(task.status) if task.status else "",
                            "priority": str(task.priority) if task.priority else "",
                            "assigned_to_id": (
                                task.assigned_to.pk if task.assigned_to else None
                            ),
                            "due_date": str(task.due_date) if task.due_date else "",
                            "project_id": task.project.pk,
                            "project_name": (
                                task.project.project_name if task.project else ""
                            ),
                        },
                        occurred_at=occurred_at.isoformat(),
                    )
                    created["task_created"] += 1
                    created["global_logs"] += 1

                elif event == "task_delete":
                    task = random.choice(tasks)
                    actor = self._pick_actor(task.project.pk, members_by_project, users)
                    AuditService.deleted(
                        module=AuditModule.TASK,
                        actor=actor,
                        target_type=TaskModel.__name__,
                        target_id=task.pk,
                        target_label=task.title or "",
                        project=task.project,
                        description=f'Deleted task "{task.title}"',
                        metadata={
                            "task_title": task.title or "",
                            "project_id": task.project.pk,
                            "project_name": (
                                task.project.project_name if task.project else ""
                            ),
                        },
                        occurred_at=occurred_at.isoformat(),
                    )
                    created["task_deleted"] += 1
                    created["global_logs"] += 1

                elif event == "comment_create":
                    comment = random.choice(comments) if comments else None
                    if not comment:
                        continue
                    actor = comment.author or self._pick_actor(
                        comment.task.project.pk if comment.task else None,
                        members_by_project,
                        users,
                    )
                    project = comment.task.project if comment.task else None
                    task = comment.task
                    AuditService.created(
                        module=AuditModule.COMMENT,
                        actor=actor,
                        target=comment,
                        project=project,
                        description=(
                            f'Added comment on task "{task.title}"'
                            if task
                            else "Added comment"
                        ),
                        metadata={
                            "comment_id": comment.pk,
                            "task_id": task.pk if task else None,
                            "task_title": task.title if task else "",
                            "project_id": project.pk if project else None,
                            "project_name": project.project_name if project else "",
                            "content_preview": (comment.content or "")[:120],
                        },
                        occurred_at=occurred_at.isoformat(),
                    )
                    created["comment_created"] += 1
                    created["global_logs"] += 1

                elif event == "project_update":
                    project = random.choice(projects)
                    actor = self._pick_actor(project.pk, members_by_project, users)
                    field = random.choice(
                        ["status", "priority", "end_date", "description"]
                    )

                    before = ""
                    after = ""

                    if field == "status":
                        before = str(project.status) if project.status else ""
                        after = random.choice([x.value for x in StatusEnum])
                    elif field == "priority":
                        before = str(project.priority) if project.priority else ""
                        after = random.choice([x.value for x in PriorityEnum])
                    elif field == "end_date":
                        before = str(project.end_date) if project.end_date else ""
                        after = str(
                            (project.end_date or timezone.now().date())
                            + timedelta(days=random.choice([7, 14, 21, 30]))
                        )
                    else:
                        before = (project.description or "")[:120]
                        after = fake.paragraph(nb_sentences=2)[:220]

                    AuditService.updated(
                        module=AuditModule.PROJECT,
                        actor=actor,
                        target=project,
                        project=project,
                        description=f'Updated project "{project.project_name}"',
                        metadata={
                            "project_name": project.project_name,
                            "project_id": project.pk,
                            "changes": {field: {"old": before, "new": after}},
                        },
                        occurred_at=occurred_at.isoformat(),
                    )
                    created["project_updated"] += 1
                    created["global_logs"] += 1

                elif event == "user_registered":
                    target_user = random.choice(users)
                    AuditService.registered(
                        actor=target_user,
                        target=target_user,
                        description=f'User "{target_user.username}" registered',
                        metadata={
                            "user_id": target_user.pk,
                            "username": target_user.username,
                            "email": target_user.email or "",
                            "first_name": target_user.first_name or "",
                            "last_name": target_user.last_name or "",
                        },
                        occurred_at=occurred_at.isoformat(),
                    )
                    created["user_registered"] += 1
                    created["global_logs"] += 1

                if (idx + 1) % 50 == 0:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  Processed {idx + 1}/{target_entries} events..."
                        )
                    )

            # Add a few realistic "burst days" for dashboard activity spikes.
            self._seed_busy_bursts(
                fake=fake,
                days_back=days_back,
                tasks=tasks,
                task_state=task_state,
                users=users,
                members_by_project=members_by_project,
                created=created,
            )

        self.stdout.write("\n" + "=" * 64)
        self.stdout.write(self.style.SUCCESS("Audit seeding complete"))
        self.stdout.write(
            self.style.SUCCESS(f"GlobalAuditLog created: {created['global_logs']}")
        )
        self.stdout.write(
            self.style.SUCCESS(f"TaskHistoryModel created: {created['task_history']}")
        )

        self.stdout.write(self.style.NOTICE("\nBreakdown:"))
        for key, value in created.items():
            if key not in ("global_logs", "task_history"):
                self.stdout.write(f"  {key}: {value}")

        module_counts = (
            GlobalAuditLog.objects.values("module")
            .order_by("module")
            .annotate(count_id=models.Count("id"))
        )
        self.stdout.write(self.style.NOTICE("\nGlobal audit distribution by module:"))
        for row in module_counts:
            self.stdout.write(f"  {row['module']}: {row['count_id']}")

        field_counts = (
            TaskHistoryModel.objects.values("field_changed")
            .order_by("field_changed")
            .annotate(count_id=models.Count("id"))
        )
        self.stdout.write(self.style.NOTICE("\nTask history distribution by field:"))
        for row in field_counts:
            self.stdout.write(f"  {row['field_changed']}: {row['count_id']}")

        recent = GlobalAuditLog.objects.select_related("actor", "project").order_by(
            "-occurred_at"
        )[:5]
        self.stdout.write(self.style.NOTICE("\nMost recent global audit entries:"))
        for log in recent:
            actor_name = log.actor.username if log.actor else "system"
            self.stdout.write(
                f"  {log.occurred_at:%Y-%m-%d %H:%M} | {actor_name} | "
                f"{log.module}:{log.action} | {log.description}"
            )
        self.stdout.write("=" * 64)

    @staticmethod
    def _pick_actor(project_id, members_by_project, users):
        if project_id and members_by_project.get(project_id):
            return random.choice(members_by_project[project_id])
        return random.choice(users)

    def _create_task_update(
        self,
        *,
        task,
        state,
        users,
        members_by_project,
        occurred_at,
    ):
        if not task:
            return False

        project = task.project
        actor = self._pick_actor(task.project_id, members_by_project, users)
        current = state.get(task.id)
        if not current:
            return False

        field_weights = {
            TaskFieldEnum.STATUS: 34,
            TaskFieldEnum.ASSIGNED_TO: 24,
            TaskFieldEnum.PRIORITY: 20,
            TaskFieldEnum.DUE_DATE: 12,
            TaskFieldEnum.TITLE: 6,
            TaskFieldEnum.DESCRIPTION: 4,
        }
        fields = []
        for field_enum, w in field_weights.items():
            fields.extend([field_enum] * w)
        field_enum = random.choice(fields)

        old_value = current[field_enum.value]
        new_value = old_value

        if field_enum == TaskFieldEnum.STATUS:
            transitions = {
                "": ["TO_DO"],
                "TO_DO": ["IN_PROGRESS", "IN_REVIEW"],
                "IN_PROGRESS": ["IN_REVIEW", "TO_DO", "DONE"],
                "IN_REVIEW": ["DONE", "IN_PROGRESS"],
                "DONE": ["IN_PROGRESS"],
            }
            new_value = random.choice(transitions.get(old_value, ["TO_DO"]))

        elif field_enum == TaskFieldEnum.PRIORITY:
            choices = [x.value for x in PriorityEnum if x.value != old_value]
            new_value = random.choice(choices) if choices else old_value

        elif field_enum == TaskFieldEnum.ASSIGNED_TO:
            pool = members_by_project.get(task.project_id, users)
            usernames = list({u.username for u in pool if u})
            if not usernames:
                usernames = [u.username for u in users if u]
            usernames = [u for u in usernames if u != old_value]
            if not usernames:
                usernames = [""]
            new_value = random.choice(usernames)

        elif field_enum == TaskFieldEnum.DUE_DATE:
            base = timezone.now().date()
            if old_value:
                try:
                    base = timezone.datetime.strptime(old_value, "%Y-%m-%d").date()
                except ValueError:
                    pass
            new_value = str(
                base + timedelta(days=random.choice([-14, -7, -3, 3, 7, 14, 21]))
            )

        elif field_enum == TaskFieldEnum.TITLE:
            prefixes = [
                "Implement",
                "Fix",
                "Refactor",
                "Optimize",
                "Review",
                "Document",
            ]
            topics = [
                "authentication flow",
                "dashboard metrics",
                "permission checks",
                "notification pipeline",
                "search behavior",
                "audit export endpoint",
            ]
            candidate = f"{random.choice(prefixes)} {random.choice(topics)}"
            new_value = candidate if candidate != old_value else f"{candidate} v2"

        elif field_enum == TaskFieldEnum.DESCRIPTION:
            new_value = (
                "Updated task scope, acceptance criteria, and edge cases after review."
                if old_value
                else "Initial scoped description with implementation notes."
            )

        if new_value == old_value:
            return False

        # Keep TaskHistory in sync with task audit metadata.
        TaskHistoryModel.objects.create(
            task=task,
            changed_by=actor,
            field_changed=field_enum,
            old_value=old_value,
            new_value=new_value,
            timestamp=occurred_at,
        )

        current[field_enum.value] = new_value

        is_completion = (
            field_enum == TaskFieldEnum.STATUS and str(new_value).upper() == "DONE"
        )

        AuditService.updated(
            module=AuditModule.TASK,
            actor=actor,
            target=task,
            project=project,
            description=(
                f'Completed task "{task.title}"'
                if is_completion
                else f'Updated task "{task.title}"'
            ),
            metadata={
                "task_id": task.id,
                "task_title": task.title or "",
                "project_id": project.id if project else None,
                "project_name": project.project_name if project else "",
                "changes": {
                    field_enum.value: {
                        "old": old_value,
                        "new": new_value,
                    }
                },
            },
            occurred_at=occurred_at,
        )
        return True

    def _seed_busy_bursts(
        self,
        *,
        fake,
        days_back,
        tasks,
        task_state,
        users,
        members_by_project,
        created,
    ):
        bursts = random.randint(3, 5)
        for _ in range(bursts):
            base_day = fake.date_time_between(
                start_date=f"-{days_back}d",
                end_date="-1d",
                tzinfo=timezone.get_current_timezone(),
            )
            entries = random.randint(12, 24)
            for _ in range(entries):
                occurred_at = base_day + timedelta(
                    hours=random.randint(8, 18),
                    minutes=random.randint(0, 59),
                )
                task = random.choice(tasks)
                ok = self._create_task_update(
                    task=task,
                    state=task_state,
                    users=users,
                    members_by_project=members_by_project,
                    occurred_at=occurred_at,
                )
                if ok:
                    created["task_updates"] += 1
                    created["global_logs"] += 1
                    created["task_history"] += 1
