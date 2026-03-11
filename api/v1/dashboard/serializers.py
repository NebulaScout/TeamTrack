from rest_framework import serializers
from django.contrib.auth.models import User


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


class AdminQuickActions(serializers.Serializer):
    overdue_tasks = OverdueTaskSerializer(many=True)
    unassigned_tasks = UnassignedTaskSerializer(many=True)
    recent_activity = AdminActivitySerializer(many=True)
