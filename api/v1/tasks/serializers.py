from rest_framework import serializers
from django.utils import timezone

# from projects.models import ProjectsModel
from tasks.models import TaskModel
from ..accounts.serializers import UserSerializer
# from ..projects.serializers import ProjectsSerializer

class TaskSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True) # cannot be modified by a user

    class Meta:
        model = TaskModel
        fields = '__all__'
        read_only_fields = ['id', 'created_by', 'created_at', 'project']


class ExtendedUserSerializer(UserSerializer):
    user_assigned_tasks = TaskSerializer(source='assigned_tasks', many=True, read_only=True)
    created_tasks = TaskSerializer(many=True, read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['assigned_tasks', 'created_tasks']
