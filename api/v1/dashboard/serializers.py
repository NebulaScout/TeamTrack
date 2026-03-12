from rest_framework import serializers
from django.utils import timezone
from django.contrib.auth.models import User

from projects.models import ProjectsModel
from tasks.models import TaskModel
from core.services.enums import StatusEnum, PriorityEnum


class DashboardUserSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(source="profile.avatar", read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "avatar"]


class TaskStatSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    change_pct = serializers.FloatField(allow_null=True)


class DashboardStatsSerializer(serializers.Serializer):
    total_tasks = TaskStatSerializer()
    completed = TaskStatSerializer()
    in_progress = TaskStatSerializer()
    overdue = TaskStatSerializer()


class ProjectProgressSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    project_name = serializers.CharField()
    total_tasks = serializers.IntegerField()
    completed_tasks = serializers.IntegerField()
    progress_pct = serializers.FloatField()


class UpcomingDeadlineSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    project_name = serializers.CharField()
    due_date = serializers.DateField()
    priority = serializers.CharField()
    assigned_to = DashboardUserSerializer(allow_null=True)


class ActivitySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    actor = DashboardUserSerializer()
    action_type = serializers.ChoiceField(
        choices=["task_completed", "comment_added", "member_joined", "task_updated"]
    )
    description = serializers.CharField()
    target_name = serializers.CharField()
    target_id = serializers.IntegerField(allow_null=True)
    timestamp = serializers.DateTimeField()


class DashboardSerializer(serializers.Serializer):
    stats = DashboardStatsSerializer()
    project_progress = ProjectProgressSerializer(many=True)
    recent_activity = ActivitySerializer(many=True)
    upcoming_deadlines = UpcomingDeadlineSerializer(many=True)


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
    project_name = serializers.CharField()
    priority = serializers.CharField(allow_null=True)


class AdminActivitySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    action_type = serializers.ChoiceField(
        choices=["user_registered", "task_completed", "comment_added", "task_updated"]
    )
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
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "avatar"]

    def get_avatar(self, obj):
        request = self.context.get("request")
        if hasattr(obj, "profile") and obj.profile and obj.profile.avatar:
            return (
                request.build_absolute_uri(obj.profile.avatar.url)
                if request
                else obj.profile.avatar.url
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
        member_users = [m.project_member for m in obj.members.all()]
        return AdminProjectMemberSerializer(
            member_users, many=True, context=self.context
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
