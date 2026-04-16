from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError as DjangoValidationError

from projects.models import ProjectsModel, ProjectMembers
from ..accounts.serializers import UserSerializer
from ..tasks.serializers import TaskSerializer
from core.services.enums import RoleEnum


ROLE_MAP = {
    "ADMIN": "Admin",
    "PROJECT_MANAGER": "Project Manager",
    "DEVELOPER": "Developer",
    "GUEST": "Guest",
}


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


class ProjectListSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)  # get only user id
    members = ProjectMemberSerializer(many=True, read_only=True)

    class Meta:
        model = ProjectsModel
        fields = [
            "id",
            "project_name",
            "description",
            "start_date",
            "end_date",
            "status",
            "members",
            "created_by",
        ]


class ProjectsDetailSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    members = ProjectMemberSerializer(many=True, read_only=True)

    class Meta:
        model = ProjectsModel
        fields = "__all__"


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
