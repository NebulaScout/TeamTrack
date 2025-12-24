from rest_framework import serializers

from tasks.models import TaskModel, CommentModel, TaskHistoryModel
from ..accounts.serializers import UserSerializer

class TaskHistorySerailizer(serializers.ModelSerializer):
    class Meta:
        model = TaskHistoryModel
        fields = '__all__'
        read_only_fields = ['id', 'task', 'changed_by', 'timestamp']

class CommentSerializer(serializers.ModelSerializer):

    class Meta:
        model = CommentModel
        fields = ['id', 'task', 'author', 'content', 'created_at']
        read_only_fields = ['id', 'created_at', 'author', 'task'] # Exclude these fields in the input, include them in the response
class TaskSerializer(serializers.ModelSerializer):
    comments = CommentSerializer(many=True, read_only=True)
    history = TaskHistorySerailizer(many=True, read_only=True)

    class Meta:
        model = TaskModel
        fields = '__all__'
        read_only_fields = ['id', 'created_by', 'created_at', 'project', 'comments', 'history']


class ExtendedUserSerializer(UserSerializer):
    user_assigned_tasks = TaskSerializer(source='assigned_tasks', many=True, read_only=True)
    created_tasks = TaskSerializer(many=True, read_only=True)
    author_of_comment = CommentSerializer(source='task_comments', many=True, read_only=True)
    task_changes = TaskHistorySerailizer(many=True, read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['assigned_tasks', 'created_tasks', 'task_comments', 'task_changes']
