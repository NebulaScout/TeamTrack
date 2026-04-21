from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError as DjangoValidationError

from projects.models import ProjectsModel, ProjectMembers
from ..accounts.serializers import UserSerializer
from ..tasks.serializers import TaskSerializer
from core.services.enums import RoleEnum, StatusEnum


ROLE_MAP = {
    "ADMIN": "Admin",
    "PROJECT_MANAGER": "Project Manager",
    "DEVELOPER": "Developer",
    "GUEST": "Guest",
}


class ProjectProgressMixin:
    # project_progress = serializers.SerializerMethodField()

    def _compute_progress(self, obj):
        total_tasks = getattr(obj, "total_tasks", None)
        if total_tasks is None:
            total_tasks = obj.project_tasks.count()

        completed_tasks = getattr(obj, "completed_tasks", None)
        if completed_tasks is None:
            completed_tasks = obj.project_tasks.filter(status=StatusEnum.DONE).count()

        progress_pct = (
            round((completed_tasks / total_tasks) * 100, 1) if total_tasks else 0.0
        )

        return {
            "id": obj.pk,
            "project_name": obj.project_name,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "progress_pct": progress_pct,
        }

    def get_project_progress(self, obj):
        return self._compute_progress(obj)


class ProjectMemberSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="project_member.id", read_only=True)
    username = serializers.CharField(source="project_member.username", read_only=True)
    avatar = serializers.ImageField(
        source="project_member.profile.avatar", read_only=True
    )
    role = serializers.CharField(source="role_in_project", read_only=True)

    class Meta:
        model = ProjectMembers
        fields = ["id", "username", "avatar", "role"]


class ProjectWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectsModel
        fields = [
            "project_name",
            "description",
            "status",
            "priority",
            "start_date",
            "end_date",
        ]

    def validate(self, attrs):
        # Support both PUT and PATCH by falling back to instance values when needed.
        start_date = attrs.get(
            "start_date",
            getattr(self.instance, "start_date", None) if self.instance else None,
        )
        end_date = attrs.get(
            "end_date",
            getattr(self.instance, "end_date", None) if self.instance else None,
        )

        if start_date and end_date and start_date > end_date:
            raise ValidationError(
                {"end_date": "end_date must be greater than or equal to start_date"}
            )

        return attrs


class ProjectListSerializer(ProjectProgressMixin, serializers.ModelSerializer):
    name = serializers.CharField(source="project_name", read_only=True)
    startDate = serializers.DateField(source="start_date", read_only=True)
    dueDate = serializers.DateField(source="end_date", read_only=True)
    createdAt = serializers.DateField(source="created_at", read_only=True)
    createdBy = serializers.IntegerField(source="created_by_id", read_only=True)
    teamMembers = ProjectMemberSerializer(source="members", many=True, read_only=True)

    # Computed/normalized fields
    status = serializers.SerializerMethodField()
    priority = serializers.SerializerMethodField()
    totalTasks = serializers.SerializerMethodField()
    tasksCompleted = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    tasks = serializers.SerializerMethodField()

    class Meta:
        model = ProjectsModel
        fields = [
            "id",
            "name",
            "description",
            "startDate",
            "dueDate",
            "status",
            "priority",
            "progress",
            "totalTasks",
            "tasksCompleted",
            "teamMembers",
            "tasks",
            "createdBy",
            "createdAt",
        ]

    def _enum_to_value(self, value):
        if value is None:
            return None
        return value.value if hasattr(value, "value") else str(value)

    def get_status(self, obj):
        return self._enum_to_value(obj.status)

    def get_priority(self, obj):
        return self._enum_to_value(obj.priority)

    def get_totalTasks(self, obj):
        annotated = getattr(obj, "total_tasks", None)
        return annotated if annotated is not None else obj.project_tasks.count()

    def get_tasksCompleted(self, obj):
        annotated = getattr(obj, "completed_tasks", None)
        if annotated is not None:
            return annotated
        return obj.project_tasks.filter(status=StatusEnum.DONE).count()

    def get_progress(self, obj):
        total_tasks = self.get_totalTasks(obj)
        completed_tasks = self.get_tasksCompleted(obj)
        return round((completed_tasks / total_tasks) * 100) if total_tasks else 0

    def get_tasks(self, obj):
        # Return lightweight task objects; frontend still gets [] when none exist.
        task_rows = obj.project_tasks.all().only(
            "id", "title", "status", "priority", "due_date"
        )
        return [
            {
                "id": t.id,
                "title": t.title,
                "status": self._enum_to_value(t.status),
                "priority": self._enum_to_value(t.priority),
                "dueDate": t.due_date,
            }
            for t in task_rows
        ]


class ProjectsDetailSerializer(ProjectProgressMixin, serializers.ModelSerializer):
    project_progress = serializers.SerializerMethodField()
    created_by = UserSerializer(read_only=True)
    members = ProjectMemberSerializer(many=True, read_only=True)
    status = serializers.SerializerMethodField()
    priority = serializers.SerializerMethodField()

    class Meta:
        model = ProjectsModel
        fields = "__all__"

    def _enum_to_value(self, value):
        if value is None:
            return None
        return value.value if hasattr(value, "value") else str(value)

    def get_status(self, obj):
        return self._enum_to_value(obj.status)

    def get_priority(self, obj):
        return self._enum_to_value(obj.priority)


class ExtendedProjectsSerializer(ProjectsDetailSerializer):
    """Include task info in the project data response"""

    project_tasks = TaskSerializer(many=True, read_only=True)

    # 'project_name' removed
    class Meta(ProjectsDetailSerializer.Meta):
        fields = [
            "id",
            "project_name",
            "description",
            "start_date",
            "end_date",
            "created_by",
            "created_at",
            "members",
            "project_tasks",
            "project_progress",
        ]
        read_only_fields = [
            "id",
            "project_name",
            "description",
            "start_date",
            "end_date",
            "created_by",
            "created_at",
            "members",
        ]


class ExtendedUserSerializer(UserSerializer):
    """Extend the accounts user serializer to include a user's projects
    - one-to-many relationship between a user and a project"""

    projects = ProjectsDetailSerializer(many=True, read_only=True)
    project_memberships = ProjectMemberSerializer(many=True, read_only=True)
    user_assigned_tasks = TaskSerializer(
        source="assigned_tasks", many=True, read_only=True
    )
    created_tasks = TaskSerializer(many=True, read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + [
            "projects",
            "project_memberships",
            "user_assigned_tasks",
            "created_tasks",
        ]


class InviteTeamMemberSerializer(serializers.Serializer):
    """Serializer for inviting a team member to a project"""

    username = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    role = serializers.ChoiceField(RoleEnum, default=RoleEnum.DEVELOPER)

    def validate_user_info(self, data):
        """Ensure either username or email is provided"""
        if not data.get("username") and not data.get("email"):
            raise ValidationError(
                {"error": "Either username or email must be provided"}
            )
        return data

    def validate_email(self, value):
        """Validate that user with email exists"""
        if value and not User.objects.filter(email=value).exists():
            raise ValidationError("No user found with this email address")
        return value

    def validate_username(self, value):
        """Validate that user with username exists"""
        if value and not User.objects.filter(username=value).exists():
            raise ValidationError("No user found with this username")
        return value


class ProjectMemberDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for project members"""

    id = serializers.IntegerField(source="project_member.id", read_only=True)
    username = serializers.CharField(source="project_member.username", read_only=True)
    email = serializers.EmailField(source="project_member.email", read_only=True)
    first_name = serializers.CharField(
        source="project_member.first_name", read_only=True
    )
    last_name = serializers.CharField(source="project_member.last_name", read_only=True)
    avatar = serializers.SerializerMethodField()
    role = serializers.CharField(source="role_in_project", read_only=True)
    is_online = serializers.SerializerMethodField()
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = ProjectMembers
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "avatar",
            "role",
            "is_online",
            "task_count",
        ]

    def get_avatar(self, obj):
        request = self.context.get("request")
        if hasattr(obj.project_member, "profile") and obj.project_member.profile.avatar:
            if request:
                return request.build_absolute_uri(obj.project_member.profile.avatar.url)
            return obj.project_member.profile.avatar.url
        return None

    def get_is_online(self, obj):
        """Check if user was active in last 5 minutes"""
        if (
            hasattr(obj.project_member, "profile")
            and obj.project_member.profile.last_seen
        ):
            from django.utils import timezone
            from datetime import timedelta

            return timezone.now() - obj.project_member.profile.last_seen < timedelta(
                minutes=5
            )
        return False

    def get_task_count(self, obj):
        """Get task count for this user in this project"""
        return obj.project_member.assigned_tasks.filter(project=obj.project).count()


class TeamStatsSerializer(serializers.Serializer):
    """Statistics for a project team"""

    total_members = serializers.IntegerField()
    online_members = serializers.IntegerField()
    admins = serializers.IntegerField()
    project_managers = serializers.IntegerField()
    developers = serializers.IntegerField()
    guests = serializers.IntegerField()


class AddTeamMemberSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(min_value=1)
    role = serializers.CharField()

    def validate_user_id(self, value):
        if not User.objects.filter(id=value).exists():
            raise ValidationError("No user found with this user_id")
        return value

    def validate_role(self, value):
        normalized = value.strip().upper().replace(" ", "_")
        mapped_role = ROLE_MAP.get(normalized)

        if not mapped_role:
            raise ValidationError(
                "Invalid role. Allowed values: ADMIN, PROJECT_MANAGER, DEVELOPER, GUEST"
            )

        return mapped_role


class UpdateMemberRoleSerializer(serializers.Serializer):
    role = serializers.CharField()

    def validate_role(self, value):
        normalized = value.strip().upper().replace(" ", "_")
        mapped_role = ROLE_MAP.get(normalized)
        if not mapped_role:
            raise ValidationError(
                "Invalid role. Allowed values: ADMIN, PROJECT_MANAGER, DEVELOPER, GUEST"
            )
        return mapped_role
