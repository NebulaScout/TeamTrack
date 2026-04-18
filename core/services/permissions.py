from rest_framework import permissions

from core.services.roles import ROLE_PERMISSIONS
from projects.models import ProjectMembers


class IsAdminDashboardUser(permissions.BasePermission):
    """
    Allows access to dashboard-admin endpoints for:
    - superusers
    - staff users
    - users in Admin group
    """

    def has_permission(self, request, view):  # type: ignore
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return (
            user.is_superuser
            or user.is_staff
            or user.groups.filter(name="Admin").exists()
        )


class UserPermissions(permissions.BasePermission):
    """Permission class for users based on predefined role permissions"""

    def has_permission(self, request, view):  # type: ignore
        if not request.user.is_authenticated and view.action != "create":
            return False

        # Get user's groups
        user_groups = request.user.groups.values_list("name", flat=True)

        if view.action == "list":
            # only roles with view_user permission can list all users
            return any(
                # If the current request is trying to list all users,
                # allow it only if the user belongs to at least one group
                # that has the view_user permission
                "view_user" in ROLE_PERMISSIONS.get(group, [])
                for group in user_groups
            )
        elif view.action == "create":
            # Any user can register
            return True
        elif view.action in ["retrieve", "partial_update", "update"]:
            # Only authenticated users can access
            return True
        elif view.action == "destroy":
            # Only roles with delete_user permissions can delete
            return any(
                "delete_user" in ROLE_PERMISSIONS.get(group, [])
                for group in user_groups
            )
        else:
            return False

    def has_object_permission(self, request, view, obj):  # type: ignore
        """Users can access their own data or if they have the necessary permissions"""
        if request.user == obj:
            return True

        user_groups = request.user.groups.values_list("name", flat=True)

        if view.action == "retrieve":
            return any(
                "view_user" in ROLE_PERMISSIONS.get(group, []) for group in user_groups
            )
        elif view.action in ["update", "partial_update"]:
            return any(
                "change_user" in ROLE_PERMISSIONS.get(group, [])
                for group in user_groups
            )
        elif view.action == "destroy":
            return any(
                "delete_user" in ROLE_PERMISSIONS.get(group, [])
                for group in user_groups
            )

        return False


class ProjectPermissions(permissions.BasePermission):
    """Permission class for projects based on predefined role permissions"""

    def has_permission(self, request, view):  # type: ignore
        if not request.user.is_authenticated:
            return False

        if request.user.is_staff or request.user.is_superuser:
            return True

        # These actions are project-scoped; object-level checks decide access.
        team_actions = {
            "invite_team_member",
            "add_team_member",
            "update_team_member",
            "update_member_role",
            "remove_team_member",
            "list_team_members",
            "team_stats",
            "leave_project",
        }
        if view.action in team_actions:
            return True

        user_groups = request.user.groups.values_list("name", flat=True)
        permissions_map = {
            "create": "add_projectsmodel",
            "update": "change_projectsmodel",
            "partial_update": "change_projectsmodel",
            "list": "view_projectsmodel",
            "retrieve": "view_projectsmodel",
            "assign_project": "assign_projectsmodel",
            "destroy": "delete_projectsmodel",
            "tasks": "add_taskmodel",
        }

        required_permission = permissions_map.get(view.action)
        if not required_permission:
            return False

        return any(
            required_permission in ROLE_PERMISSIONS.get(group, [])
            for group in user_groups
        )

    def has_object_permission(self, request, view, obj):  # type: ignore
        """Object-level permissons for projects
        Creator of the project always has access, or user must have the appropriate permissions
        """

        if request.user.is_staff or request.user.is_superuser:
            return True

        # Project creator has full access
        if obj.created_by == request.user:
            return True

        user_groups = request.user.groups.values_list("name", flat=True)

        # For team management actions, check if user has appropriate role in THIS project
        if view.action in [
            "invite_team_member",
            "add_team_member",
            "update_team_member",
            "remove_team_member",
            "update_member_role",
        ]:
            # Check if user is Admin or Project Manager globally OR in this specific project
            has_global_permission = any(
                "add_projectmembers" in ROLE_PERMISSIONS.get(group, [])
                for group in user_groups
            )

            if has_global_permission:
                return True

            # Check project-specific role
            try:
                membership = ProjectMembers.objects.get(
                    project=obj, project_member=request.user
                )
                return membership.role_in_project in ["Admin", "Project Manager"]
            except ProjectMembers.DoesNotExist:
                return False

        # Team visibility: Admin or Project Manager only
        if view.action in ["list_team_members", "team_stats"]:
            has_global_permission = any(
                "add_projectmembers" in ROLE_PERMISSIONS.get(group, [])
                for group in user_groups
            )
            if has_global_permission:
                return True

            try:
                membership = ProjectMembers.objects.get(
                    project=obj, project_member=request.user
                )
                return membership.role_in_project in ["Admin", "Project Manager"]
            except ProjectMembers.DoesNotExist:
                return False

        # For leaving project, any member can leave
        if view.action == "leave_project":
            return ProjectMembers.objects.filter(
                project=obj, project_member=request.user
            ).exists()

        permissions_map = {
            "list": "view_projectsmodel",
            "retrieve": "view_projectsmodel",
            "update": "change_projectsmodel",
            "partial_update": "change_projectsmodel",
            "destroy": "delete_projectsmodel",
            # "assign_project": "assign_projectsmodel",
            # "add_members": "add_projectmembers",
            # "tasks": "add_taskmodel",
            # "tasks": "view_taskmodel",
        }

        required_permissions = permissions_map.get(view.action)
        if not required_permissions:
            return False

        return any(
            required_permissions in ROLE_PERMISSIONS.get(group, [])
            for group in user_groups
        )


class TaskPermissions(permissions.BasePermission):
    """Permission class for tasks based on predefined role permissions"""

    def has_permission(self, request, view):  # type: ignore
        if not request.user.is_authenticated:
            return False

        user_groups = request.user.groups.values_list("name", flat=True)

        permissions_map = {
            "create": "add_taskmodel",
            "update": "change_taskmodel",
            "list": "view_taskmodel",
            "retrieve": "view_taskmodel",
            "destroy": "delete_taskmodel",
            "update_status": "change_taskmodel",
            "update_priority": "change_taskmodel",
            "assign": "change_taskmodel",  # assign a task to a user
            "comments": "view_commentmodel",  # retrieve comments
            "comments": "add_commentmodel",  # add a comment
            "task_logs": "view_taskhistorymodel",  # view task logs
        }

        required_permission = permissions_map.get(view.action)
        if not required_permission:
            return False

        return any(
            required_permission in ROLE_PERMISSIONS.get(group, [])
            for group in user_groups
        )

    def has_object_permission(self, request, view, obj):  # type: ignore
        """Object-level permissons for tasks
        Creator of the task always has access, or user must have the appropriate permissions
        """

        if request.user.is_staff or request.user.is_superuser:
            return True

        # Task creator has full access
        if obj.created_by == request.user:
            return True

        user_groups = request.user.groups.values_list("name", flat=True)

        permissions_map = {
            "update": "change_taskmodel",
            "partial_update": "change_taskmodel",
            "retrieve": "view_taskmodel",
            "destroy": "delete_taskmodel",
            "update_status": "change_taskmodel",
            "update_priority": "change_taskmodel",
            "assign": "change_taskmodel",
            "comments": "view_commentmodel",
            "comments": "add_commentmodel",
            "task_logs": "view_taskhistorymodel",
        }

        required_permissions = permissions_map.get(view.action)
        if not required_permissions:
            return False

        return any(
            required_permissions in ROLE_PERMISSIONS.get(group, [])
            for group in user_groups
        )


class CalendarEventPermissions(permissions.BasePermission):
    """Permission class for calendar based on predefined role permissions"""

    def has_permission(self, request, view):  # type: ignore
        if not request.user.is_authenticated:
            return False

        user_groups = request.user.groups.values_list("name", flat=True)

        permissions_map = {
            "create": "add_calendarevent",
            "update": "change_calendarevent",
            "partial_update": "change_calendarevent",
            "list": "view_calendarevent",
            "retrieve": "view_calendarevent",
        }

        required_permission = permissions_map.get(view.action)
        if not required_permission:
            return False

        return any(
            required_permission in ROLE_PERMISSIONS.get(group, [])
            for group in user_groups
        )

    def has_object_permission(self, request, view, obj):  # type: ignore
        """Object-level permissons for calendar
        Creator of the event always has access, or user must have the appropriate permissions
        """

        # Event creator has full access
        if obj.created_by == request.user:
            return True

        user_groups = request.user.groups.values_list("name", flat=True)

        permissions_map = {
            "list": "view_calendarevent",
            "retrieve": "view_calendarevent",
            "update": "change_calendarevent",
            "partial_update": "change_calendarevent",
        }

        required_permissions = permissions_map.get(view.action)
        if not required_permissions:
            return False

        return any(
            required_permissions in ROLE_PERMISSIONS.get(group, [])
            for group in user_groups
        )
