from rest_framework import serializers
from django.utils import timezone
from django.contrib.auth.models import User

from projects.models import ProjectsModel, ProjectMembers
from tasks.models import TaskModel
from core.services.enums import StatusEnum, PriorityEnum
from .user_serializers import DashboardUserSerializer


# Admin Dashboard
class OverdueTaskSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    project_name = serializers.CharField()
    due_date = serializers.DateField()
    assigned_to = DashboardUserSerializer(allow_null=True)


class UnassignedTaskSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    project_id = serializers.IntegerField()
    project_name = serializers.CharField()
    priority = serializers.CharField(allow_null=True)


class AdminActivitySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    action_type = serializers.CharField()  # e.g. user_registered, project_created
    description = serializers.CharField()
    actor_name = serializers.CharField()  # display name or username
    actor_url = serializers.CharField(allow_null=True)  # profile link if needed
    timestamp = serializers.DateTimeField()


class AdminQuickActionsSerializer(serializers.Serializer):
    overdue_tasks = OverdueTaskSerializer(many=True)
    unassigned_tasks = UnassignedTaskSerializer(many=True)
    recent_activity = AdminActivitySerializer(many=True)


# User's tab
class AdminUserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    registered_on = serializers.DateTimeField(source="date_joined", read_only=True)
    project_count = serializers.IntegerField(read_only=True)
    task_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "avatar",
            "role",
            "status",
            "registered_on",
            "project_count",
            "task_count",
        ]

    def get_avatar(self, obj):
        if hasattr(obj, "profile") and obj.profile and obj.profile.avatar:
            request = self.context.get("request")
            return (
                request.build_absolute_uri(obj.profile.avatar.url)
                if request
                else obj.profile.avatar.url
            )
        return None

    def get_role(self, obj):
        group = obj.groups.first()
        return group.name if group else None

    def get_status(self, obj):
        return "active" if obj.is_active else "inactive"


class AdminUserUpdateSerializer(serializers.Serializer):
    ROLE_CHOICES = ["Admin", "Project Manager", "Developer", "Guest"]

    role = serializers.ChoiceField(choices=ROLE_CHOICES, required=False)
    is_active = serializers.BooleanField(required=False)


# Project's Tab
class AdminProjectOwnerSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "full_name", "avatar"]

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username

    def get_avatar(self, obj):
        request = self.context.get("request")
        if hasattr(obj, "profile") and obj.profile and obj.profile.avatar:
            return (
                request.build_absolute_uri(obj.profile.avatar.url)
                if request
                else obj.profile.avatar.url
            )
        return None


class AdminProjectMemberSerializer(serializers.ModelSerializer):
    # user-level fields (from related User via project_member FK)
    id = serializers.IntegerField(source="project_member.id", read_only=True)
    username = serializers.CharField(source="project_member.username", read_only=True)
    avatar = serializers.SerializerMethodField()

    # membership-level field (from ProjectMembers model itself)
    role = serializers.CharField(source="role_in_project", read_only=True)

    class Meta:
        model = ProjectMembers
        fields = [
            "id",
            "username",
            "avatar",
            "role",
        ]

    # def get_full_name(self, obj):
    #     return obj.project_member.get_full_name() or obj.project_member.username

    def get_avatar(self, obj):
        request = self.context.get("request")
        user = obj.project_member
        if hasattr(user, "profile") and user.profile and user.profile.avatar:
            return (
                request.build_absolute_uri(user.profile.avatar.url)
                if request
                else user.profile.avatar.url
            )
        return None


class AdminProjectListSerializer(serializers.ModelSerializer):
    owner = AdminProjectOwnerSerializer(source="created_by", read_only=True)
    members = serializers.SerializerMethodField()
    member_count = serializers.IntegerField(read_only=True)
    tasks_completed = serializers.IntegerField(read_only=True)
    tasks_total = serializers.IntegerField(read_only=True)

    class Meta:
        model = ProjectsModel
        fields = [
            "id",
            "project_name",
            "description",
            "status",
            "priority",
            "start_date",
            "end_date",
            "created_at",
            "owner",
            "members",
            "member_count",
            "tasks_completed",
            "tasks_total",
        ]

    def get_members(self, obj):
        memberships = obj.members.all()
        return AdminProjectMemberSerializer(
            memberships, many=True, context=self.context
        ).data


class AdminProjectWriteSerializer(serializers.ModelSerializer):
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


# Tasks Tab
class AdminTaskAssigneeSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "full_name", "avatar"]

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username

    def get_avatar(self, obj):
        request = self.context.get("request")
        if hasattr(obj, "profile") and obj.profile and obj.profile.avatar:
            return (
                request.build_absolute_uri(obj.profile.avatar.url)
                if request
                else obj.profile.avatar.url
            )
        return None


class AdminTaskListSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.project_name", read_only=True)
    assignee = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()

    class Meta:
        model = TaskModel
        fields = [
            "id",
            "title",
            "project_id",
            "project_name",
            "assignee",
            "status",
            "priority",
            "due_date",
            "is_overdue",
            "created_at",
            "updated_at",
        ]

    def get_assignee(self, obj):
        if obj.assigned_to is None:
            return None
        return AdminTaskAssigneeSerializer(obj.assigned_to, context=self.context).data

    def get_is_overdue(self, obj):

        if obj.due_date and obj.status != "DONE":
            return obj.due_date < timezone.now().date()
        return False


class AdminTaskStatsSerializer(serializers.Serializer):
    overdue_count = serializers.IntegerField()
    unassigned_count = serializers.IntegerField()


class AdminTasksResponseSerializer(serializers.Serializer):
    stats = AdminTaskStatsSerializer()
    tasks = AdminTaskListSerializer(many=True)


class AdminTaskUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=StatusEnum.choices, required=False)
    priority = serializers.ChoiceField(
        choices=PriorityEnum.choices, required=False, allow_null=True
    )
    assigned_to = serializers.IntegerField(required=False, allow_null=True)


# Audit Logs Tab
class AuditLogUserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "full_name", "avatar"]

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username

    def get_avatar(self, obj):
        request = self.context.get("request")
        if hasattr(obj, "profile") and obj.profile and obj.profile.avatar:
            return (
                request.build_absolute_uri(obj.profile.avatar.url)
                if request
                else obj.profile.avatar.url
            )
        return None


class AuditLogSerializer(serializers.Serializer):
    """
    Serializer for audit log entries showing all history changes
    """

    id = serializers.IntegerField()
    actor = AuditLogUserSerializer(allow_null=True)
    module = serializers.CharField()  # project/task/user/comment/system
    action = serializers.CharField()  # created/updated/deleted/registered
    action_type = serializers.CharField()  # combined readable key
    description = serializers.CharField()

    target_type = serializers.CharField(allow_blank=True, allow_null=True)
    target_id = serializers.IntegerField(allow_null=True)
    target_label = serializers.CharField(allow_blank=True, allow_null=True)

    project_id = serializers.IntegerField(allow_null=True)
    project_name = serializers.CharField(allow_blank=True, allow_null=True)

    metadata = serializers.JSONField(required=False)
    timestamp = serializers.DateTimeField()


class AuditLogsResponseSerializer(serializers.Serializer):
    """
    Response wrapper for audit logs endpoint
    """

    logs = AuditLogSerializer(many=True)
    total_count = serializers.IntegerField()


class AdminTaskCommentAuthorSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "full_name", "avatar"]

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username

    def get_avatar(self, obj):
        request = self.context.get("request")
        if hasattr(obj, "profile") and obj.profile and obj.profile.avatar:
            return (
                request.build_absolute_uri(obj.profile.avatar.url)
                if request
                else obj.profile.avatar.url
            )
        return None


class AdminTaskCommentSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    content = serializers.CharField()
    created_at = serializers.DateTimeField()
    author = AdminTaskCommentAuthorSerializer(allow_null=True)


class AdminTaskDetailSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.project_name", read_only=True)
    assignee = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = TaskModel
        fields = [
            "id",
            "title",
            "description",
            "project_id",
            "project_name",
            "assignee",
            "status",
            "priority",
            "due_date",
            "created_at",
            "updated_at",
            "comments_count",
            "comments",
        ]

    def get_assignee(self, obj):
        if obj.assigned_to is None:
            return None
        return AdminTaskAssigneeSerializer(obj.assigned_to, context=self.context).data

    def get_comments(self, obj):
        # Uses prefetched comments if available
        comments_qs = (
            obj.comments.all()
            .select_related("author", "author__profile")
            .order_by("-created_at")
        )
        payload = []
        for c in comments_qs:
            payload.append(
                {
                    "id": c.id,
                    "content": c.content,
                    "created_at": c.created_at,
                    "author": c.author,
                }
            )
        return AdminTaskCommentSerializer(payload, many=True, context=self.context).data

    def get_comments_count(self, obj):
        return obj.comments.count()


class AdminTaskLogSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    actor = AuditLogUserSerializer(allow_null=True)
    action_type = serializers.CharField()
    description = serializers.CharField()
    field_changed = serializers.CharField()
    old_value = serializers.CharField(allow_null=True)
    new_value = serializers.CharField(allow_null=True)
    timestamp = serializers.DateTimeField()


class AdminTaskLogsResponseSerializer(serializers.Serializer):
    task_id = serializers.IntegerField()
    task_title = serializers.CharField()
    logs = AdminTaskLogSerializer(many=True)
    total_count = serializers.IntegerField()
