from rest_framework import serializers

from projects.models import ProjectsModel
from ..accounts.serializers import UserSerializer

class ProjectsSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    class Meta:
        model = ProjectsModel
        fields = '__all__'

class ExtendedUserSerializer(UserSerializer):
    """Extend the accounts user serializer to include a user's projects
    - one-to-many relationship between a user and a project"""
    projects = ProjectsSerializer(source='projects', many=True, read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['projects']
    