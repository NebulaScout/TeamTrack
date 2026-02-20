from rest_framework import serializers
from django.contrib.auth.models import User
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes

from accounts.models import RegisterModel, UserProfile
from core.services.registration_service import register_user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    role = serializers.SerializerMethodField()
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id' ,'username', 'first_name', 'last_name', 'email','password', 'confirm_password',
                  'role', 'profile']
        
    def get_role(self, obj):
        """Return a users primary role"""
        group = obj.groups.first()
        return group.name if group else None

 
class RegistrationSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = RegisterModel
        fields = '__all__'

    def create(self, validated_data):
        user_data = validated_data.pop('user')

        try:

            return register_user(
                first_name = user_data["first_name"],
                last_name = user_data["last_name"],
                username = user_data["username"],
                email = user_data["email"],
                password = user_data["password"],
            )
        except ValueError as exc:
            raise serializers.ValidationError({"user": {"email": [str(exc)]}})

class UserListSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()
    task_count = serializers.SerializerMethodField()
    projects = serializers.SerializerMethodField()

    class Meta: 
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'avatar',
                  'role', 'is_online', 'task_count', 'projects']
    
    @extend_schema_field(OpenApiTypes.URI)
    def get_avatar(self, obj):
        if hasattr(obj, 'profile') and obj.profile.avatar:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.profile.avatar.url) if request else obj.profile.avatar.url
        return None

    @extend_schema_field(OpenApiTypes.STR)
    def get_role(self, obj):
        # Get primary role from first project membership
        membership = obj.project_memberships.first()
        return membership.role_in_project if membership else 'Guest'
    
    @extend_schema_field(OpenApiTypes.BOOL)
    def get_is_online(self, obj):
        return False 
    
    @extend_schema_field(OpenApiTypes.INT)
    def get_task_count(self, obj):
        return obj.task_count # uses the annotated value

    @extend_schema_field(serializers.ListField(child=serializers.IntegerField()))
    def get_projects(self, obj):
        # uses the prefetched query
        return [pm.project_id for pm in obj.project_memberships.all()]

class TeamStatsSerializer(serializers.Serializer):
    total_members = serializers.IntegerField()
    online_members = serializers.IntegerField()
    admin_members = serializers.IntegerField()