from rest_framework import serializers

from tasks.models import TaskModel, CommentModel, TaskHistoryModel
from ..accounts.serializers import UserSerializer


# Mini serializer for user info in tasks list
class AssignedUserSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(source="profile.avatar", read_only=True)
    role = serializers.SerializerMethodField()

    class Meta:
        model = UserSerializer.Meta.model
        fields = ["id", "username", "avatar", "role"]

        def get_role(self, obj):
            """Return users primary role"""
            group = obj.groups.first()
            return group.name if group else None


class CommentWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model: CommentModel
        fields = ["content"]


class CommentSerializer(serializers.ModelSerializer):
    author = AssignedUserSerializer(read_only=True)

    class Meta:
        model = CommentModel
        fields = ["id", "task", "author", "content", "created_at"]
        read_only_fields = [
            "id",
            "created_at",
            "author",
            "task",
        ]


# Write serializer for creating and updating tasks
class TaskWriteSerializer(serializers.ModelSerializer):
    # project = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = TaskModel
        fields = [
            "title",
            "description",
            "assigned_to",
            "status",
            "priority",
            "due_date",
            # "project",
        ]


class TaskListSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    assigned_to = serializers.PrimaryKeyRelatedField(read_only=True)
    project = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = TaskModel
        fields = [
            "id",
            "title",
            "description",
            "status",
            "priority",
            "due_date",
            "created_by",
            "assigned_to",
            "project",
        ]


class TaskDetailSerializer(serializers.ModelSerializer):
    created_by = AssignedUserSerializer(read_only=True)
    assigned_to = AssignedUserSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = TaskModel
        fields = [
            "id",
            "title",
            "description",
            "status",
            "priority",
            "due_date",
            "assigned_to",
            "project",
            "comments",
            "created_by",
        ]


class TaskHistorySerializer(serializers.ModelSerializer):
    changed_by = AssignedUserSerializer(read_only=True)

    class Meta:
        model = TaskHistoryModel
        fields = "__all__"
        read_only_fields = ["id", "task", "changed_by", "timestamp"]


class TaskSerializer(serializers.ModelSerializer):
    comments = CommentSerializer(many=True, read_only=True)
    history = TaskHistorySerializer(many=True, read_only=True)

    class Meta:
        model = TaskModel
        fields = "__all__"
        read_only_fields = [
            "id",
            "created_by",
            "created_at",
            "project",
            "comments",
            "history",
        ]


#! Keep at bottom to avoid circular imports
class ExtendedUserSerializer(UserSerializer):
    user_assigned_tasks = TaskSerializer(
        source="assigned_tasks", many=True, read_only=True
    )
    created_tasks = TaskListSerializer(many=True, read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + [
            "user_assigned_tasks",
            "created_tasks",
        ]
