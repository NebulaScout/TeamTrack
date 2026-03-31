from rest_framework import viewsets, status
from django.contrib.auth.models import User
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from django.db.models import Count, Prefetch
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from drf_spectacular.types import OpenApiTypes

from .serializers import (
    RegistrationSerializer,
    UserSerializer,
    UserProfileSerializer,
    UserListSerializer,
    TeamStatsSerializer,
)
from accounts.models import RegisterModel, UserProfile
from core.services.permissions import UserPermissions
from core.services.group_assignment import set_user_role
from projects.models import ProjectMembers
from ..projects.serializers import ExtendedUserSerializer
from api.v1.common.responses import ResponseMixin


class RegisterAPIView(ResponseMixin, APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
        except ValidationError as exc:
            return self._error(
                "VALIDATION_ERROR",
                "Email already exists",
                exc.detail,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return self._success(
            message="Registration Successful", status_code=status.HTTP_201_CREATED
        )


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [UserPermissions]


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [UserPermissions]


class TeamUserViewSet(ResponseMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = UserListSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def _is_admin_or_project_manager(self, user):
        return user.is_staff or user.groups.filter(name="Project Manager").exists()

    def _forbidden_response(self):
        return self._error(
            "FORBIDDEN",
            "Admin or Project Manager access required.",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    def get_queryset(self):  # type: ignore
        queryset = (
            User.objects.select_related("profile")
            .prefetch_related("project_memberships__project")
            .annotate(task_count=Count("assigned_tasks"))
        )

        if self.request.user.is_staff:
            return queryset

        manager_project_ids = ProjectMembers.objects.filter(
            project_member=self.request.user
        ).values_list("project_id", flat=True)

        return queryset.filter(
            project_memberships__project_id__in=manager_project_ids
        ).distinct()

    def list(self, request, *args, **kwargs):
        if not self._is_admin_or_project_manager(request.user):
            return self._forbidden_response()
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        if not self._is_admin_or_project_manager(request.user):
            return self._forbidden_response()
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(responses=TeamStatsSerializer)
    @action(detail=False, methods=["get"], url_path="stats")
    def team_stats(self, request):
        """Get tam statistics for the current user's projects"""
        if not self._is_admin_or_project_manager(request.user):
            return self._forbidden_response()

        if request.user.is_staff:
            user_projects = ProjectMembers.objects.values_list("project_id", flat=True)
        else:
            user_projects = request.user.project_memberships.values_list(
                "project_id", flat=True
            )

        # Get all projects te user is a member of
        # get all users in those projects
        team_members = User.objects.filter(
            project_memberships__project_id__in=user_projects
        ).distinct()

        # Calculate stats
        stats = {
            "total_members": team_members.count(),
            "online_members": team_members.filter(
                profile__last_seen__isnull=False
            ).count(),
            "admin_members": ProjectMembers.objects.filter(
                project_id__in=user_projects, role_in_project="Admin"
            ).count(),
        }

        return self._success(data=stats)
