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
from core.services.audit_service import AuditService
from core.services.enums import AuditModule
from core.services.permissions import IsAdminDashboardUser


class AdminUsersView(ResponseMixin, APIView):
    """
    GET  /dashboard/admin/users/  — list all users with search & filters
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminDashboardUser]

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
    permission_classes = [IsAdminDashboardUser]

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

        first_group = user.groups.first() if user else None
        before = {
            "role": first_group.name if first_group else None,
            "is_active": user.is_active,
        }

        serializer = AdminUserUpdateSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return self._error(
                "VALIDATION_ERROR",
                "Invalid data.",
                serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        update_fields = []

        if isinstance(data, dict) and "role" in data:
            try:
                group = Group.objects.get(name=data["role"])
            except Group.DoesNotExist:
                return self._error(
                    "NOT_FOUND",
                    f'Role "{data["role"]}" does not exist.',
                    status_code=status.HTTP_404_NOT_FOUND,
                )
            # user.groups.clear()
            # user.groups.add(group)
            user.groups.set([group])

            # Keep IsAdminUser-compatible admin checks in sync
            should_be_staff = group.name == "Admin" or user.is_superuser
            if user.is_staff != should_be_staff:
                user.is_staff = should_be_staff
                update_fields.append("is_staff")

        if isinstance(data, dict) and "is_active" in data:
            if user.is_active != data["is_active"]:
                user.is_active = data["is_active"]
                update_fields.append("is_active")

        if update_fields:
            user.save(update_fields=update_fields)

        updated_user = self._get_user(pk)
        first_group = updated_user.groups.first() if updated_user else None
        after = {
            "role": first_group.name if first_group else None,
            "is_active": updated_user.is_active if updated_user else None,
        }

        changed_fields = {}
        for field, old_value in before.items():
            new_value = after.get(field)
            if old_value != new_value:
                changed_fields[field] = {"old": old_value, "new": new_value}

        if changed_fields and updated_user:
            AuditService.updated(
                module=AuditModule.USER,
                actor=request.user,
                target=updated_user,
                description=f'Updated user "{updated_user.username}"',
                metadata={
                    "user_id": updated_user.pk,
                    "username": updated_user.username,
                    "changes": changed_fields,
                },
            )
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
