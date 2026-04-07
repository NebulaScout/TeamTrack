from rest_framework import status
from drf_spectacular.utils import extend_schema

from django.contrib.auth.models import User, Group
from django.db.models import Count, Q
from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from api.v1.common.responses import ResponseMixin
from ..serializers.admin_serializers import (
    AdminUserSerializer,
    AdminUserUpdateSerializer,
)


class AdminUsersView(ResponseMixin, APIView):
    """
    GET  /dashboard/admin/users/  — list all users with search & filters
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]

    @extend_schema(responses=AdminUserSerializer(many=True))
    def get(self, request):
        queryset = (
            User.objects.select_related("profile")
            .prefetch_related("groups")
            .annotate(
                project_count=Count("project_memberships", distinct=True),
                task_count=Count("assigned_tasks", distinct=True),
            )
            .order_by("-date_joined")
        )

        search = request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search)
                | Q(email__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
            )

        role = request.query_params.get("role", "").strip()
        if role:
            queryset = queryset.filter(groups__name=role)

        status_filter = request.query_params.get("status", "").strip()
        if status_filter == "active":
            queryset = queryset.filter(is_active=True)
        elif status_filter == "inactive":
            queryset = queryset.filter(is_active=False)

        serializer = AdminUserSerializer(
            queryset, many=True, context={"request": request}
        )
        return self._success(
            data=serializer.data, message="Users retrieved successfully"
        )


class AdminUserDetailView(ResponseMixin, APIView):
    """
    GET    /dashboard/admin/users/<pk>/  — user detail
    PATCH  /dashboard/admin/users/<pk>/  — update role and/or active status
    DELETE /dashboard/admin/users/<pk>/  — delete user
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]

    def _get_user(self, pk):
        try:
            return (
                User.objects.select_related("profile")
                .prefetch_related("groups")
                .annotate(
                    project_count=Count("project_memberships", distinct=True),
                    task_count=Count("assigned_tasks", distinct=True),
                )
                .get(pk=pk)
            )
        except User.DoesNotExist:
            return None

    @extend_schema(responses=AdminUserSerializer)
    def get(self, request, pk):
        user = self._get_user(pk)
        if not user:
            return self._error(
                "NOT_FOUND", "User not found.", status_code=status.HTTP_404_NOT_FOUND
            )
        serializer = AdminUserSerializer(user, context={"request": request})
        return self._success(data=serializer.data)

    @extend_schema(request=AdminUserUpdateSerializer, responses=AdminUserSerializer)
    def patch(self, request, pk):
        user = self._get_user(pk)
        if not user:
            return self._error(
                "NOT_FOUND", "User not found.", status_code=status.HTTP_404_NOT_FOUND
            )

        if user == request.user:
            return self._error(
                "FORBIDDEN",
                "You cannot modify your own account via this endpoint.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        serializer = AdminUserUpdateSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return self._error(
                "VALIDATION_ERROR",
                "Invalid data.",
                serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data

        if isinstance(data, dict) and "role" in data:
            try:
                group = Group.objects.get(name=data["role"])
            except Group.DoesNotExist:
                return self._error(
                    "NOT_FOUND",
                    f'Role "{data["role"]}" does not exist.',
                    status_code=status.HTTP_404_NOT_FOUND,
                )
            user.groups.clear()
            user.groups.add(group)

        if isinstance(data, dict) and "is_active" in data:
            user.is_active = data["is_active"]
            user.save(update_fields=["is_active"])

        updated_user = self._get_user(pk)
        return self._success(
            data=AdminUserSerializer(updated_user, context={"request": request}).data,
            message="User updated successfully.",
        )

    def delete(self, request, pk):
        user = self._get_user(pk)
        if not user:
            return self._error(
                "NOT_FOUND", "User not found.", status_code=status.HTTP_404_NOT_FOUND
            )

        if user == request.user:
            return self._error(
                "FORBIDDEN",
                "You cannot delete your own account.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        username = user.username
        user.delete()
        return self._success(message=f'User "{username}" deleted successfully.')
