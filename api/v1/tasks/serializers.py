from rest_framework import serializers
from django.utils import timezone

from tasks.models import TaskModel, CommentModel
from ..accounts.serializers import UserSerializer

class CommentSerializer(serializers.ModelSerializer):

    class Meta:
        model = CommentModel
        fields = ['id', 'task', 'author', 'content', 'created_at']
        read_only_fields = ['id', 'created_at', 'author', 'task'] # Exclude these fields in the input, include them in the response
class TaskSerializer(serializers.ModelSerializer):
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = TaskModel
        fields = '__all__'
        read_only_fields = ['id', 'created_by', 'created_at', 'project', 'comments']


class ExtendedUserSerializer(UserSerializer):
    user_assigned_tasks = TaskSerializer(source='assigned_tasks', many=True, read_only=True)
    created_tasks = TaskSerializer(many=True, read_only=True)
    author_of_comment = CommentSerializer(source='author', many=True, read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['assigned_tasks', 'created_tasks', 'author']
