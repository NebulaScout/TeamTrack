from rest_framework import serializers

from projects.models import ProjectsModel
from ..accounts.serializers import UserSerializer

# TODO: Add Authentication & authorization
class ProjectsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectsModel
        fields = '__all__'

class ExtendedUserSerializer(UserSerializer):
    projects = ProjectsSerializer(source='projects', many=True, read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['projects']
    