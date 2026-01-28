from rest_framework import serializers

from projects.models import ProjectsModel, ProjectMembers
from ..accounts.serializers import UserSerializer
from ..tasks.serializers import TaskSerializer

class ProjectMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectMembers
        fields = '__all__'
        read_only_fields = ['project']

class ProjectsSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    members = ProjectMemberSerializer(many=True, read_only=True)
    class Meta:
        model = ProjectsModel
        fields = '__all__'

class ExtendedProjectsSerializer(ProjectsSerializer):
    """Include task info in the project data response"""
    project_tasks = TaskSerializer(many=True, read_only=True)    

# 'project_name' removed
    class Meta(ProjectsSerializer.Meta):
        fields = ['id', 'project_name', 'description', 'start_date', 'end_date', 
                  'created_by', 'created_at', 'members', 'project_tasks']
        read_only_fields = ['id', 'project_name', 'description', 'start_date', 'end_date', 
                  'created_by', 'created_at', 'members']


class ExtendedUserSerializer(UserSerializer):
    """Extend the accounts user serializer to include a user's projects
    - one-to-many relationship between a user and a project"""
    projects = ProjectsSerializer(many=True, read_only=True)
    project_memberships = ProjectMemberSerializer(many=True, read_only=True)
    user_assigned_tasks = TaskSerializer(source='assigned_tasks', many=True, read_only=True)
    created_tasks = TaskSerializer(many=True, read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['projects', 'project_memberships', 'user_assigned_tasks', 'created_tasks']

    