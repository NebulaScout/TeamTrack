from rest_framework import serializers

from projects.models import ProjectsModel, ProjectMembers
from ..accounts.serializers import UserSerializer
from ..tasks.serializers import TaskSerializer


class ProjectMemberSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="project_member.id", read_only=True)
    username = serializers.CharField(source="project_memebr.username", read_only=True)
    avatar = serializers.ImageField(
        source="project_member.profile.avatar", read_only=True
    )
    role = serializers.CharField(source="role_in_project", read_only=True)

    class Meta:
        model = ProjectMembers
        fields = ["id", "username", "avatar", "role"]


class ProjectWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectsModel
        fields = [
            "project_name",
            "description",
            "status",
            "priority",
            "start_date",
            "end_date",
            "created_by",
        ]


class ProjectListSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)  # get only user id
    members = ProjectMemberSerializer(many=True, read_only=True)

    class Meta:
        model = ProjectsModel
        fields = [
            "id",
            "project_name",
            "description",
            "end_date",
            "status",
            "members",
            "created_by",
        ]


class ProjectsDetailSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    members = ProjectMemberSerializer(many=True, read_only=True)

    class Meta:
        model = ProjectsModel
        fields = "__all__"


class ExtendedProjectsSerializer(ProjectsDetailSerializer):
    """Include task info in the project data response"""

    project_tasks = TaskSerializer(many=True, read_only=True)

    # 'project_name' removed
    class Meta(ProjectsDetailSerializer.Meta):
        fields = [
            "id",
            "project_name",
            "description",
            "start_date",
            "end_date",
            "created_by",
            "created_at",
            "members",
            "project_tasks",
        ]
        read_only_fields = [
            "id",
            "project_name",
            "description",
            "start_date",
            "end_date",
            "created_by",
            "created_at",
            "members",
        ]


class ExtendedUserSerializer(UserSerializer):
    """Extend the accounts user serializer to include a user's projects
    - one-to-many relationship between a user and a project"""

    projects = ProjectsDetailSerializer(many=True, read_only=True)
    project_memberships = ProjectMemberSerializer(many=True, read_only=True)
    user_assigned_tasks = TaskSerializer(
        source="assigned_tasks", many=True, read_only=True
    )
    created_tasks = TaskSerializer(many=True, read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + [
            "projects",
            "project_memberships",
            "user_assigned_tasks",
            "created_tasks",
        ]
