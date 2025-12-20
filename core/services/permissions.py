from rest_framework import permissions

from core.services.roles import ROLE_PERMISSIONS

class UserPermissions(permissions.BasePermission):
    """Permission class for users based on predefined role permissions"""
    
    def has_permission(self, request, view): # type: ignore
        if not request.user.is_authenticated and view.action != 'create':
            return False

        # Get user's groups
        user_groups = request.user.groups.values_list('name', flat=True) 

        if view.action == 'list':
            # only roles with view_user permission can list all users
            return any(
                # If the current request is trying to list all users,
                # allow it only if the user belongs to at least one group
                # that has the view_user permission
                    
               'view_user' in ROLE_PERMISSIONS.get(group, [])
               for group in user_groups
            )
        elif view.action == 'create':
            # Any user can register
            return True
        elif view.action in ['retrieve', 'partial_update', 'update']:
            # Only authenticated users can access
            return True
        elif view.action == 'destroy':
            # Only roles with delete_user permissions can delete
            return any(
                'delete_user' in ROLE_PERMISSIONS.get(group, [])
                for group in user_groups
            )
        else:
            return False
        
    def has_object_permission(self, request, view, obj): # type: ignore
        """Users can access their own data or if they have the necessary permissions"""
        if request.user == obj:
            return True
        
        user_groups = request.user.groups.values_list('name', flat=True)

        if view.action == 'retrieve':
            return any(
                'view_user' in ROLE_PERMISSIONS.get(group, [])
                for group in user_groups
            )
        elif view.action in ['update', 'partial_update']:
            return any(
                'change_user' in ROLE_PERMISSIONS.get(group, [])
                for group in user_groups
            )
        elif view.action == 'destroy':
            return any(
                'delete_user' in ROLE_PERMISSIONS.get(group, [])
                for group in user_groups
            )
        
        return False
    
class ProjectPermissions(permissions.BasePermission):
    """Permission class for projects based on predefined role permissions"""

    def has_permission(self, request, view): # type: ignore
        if not request.user.is_authenticated:
            return False
        
        user_groups = request.user.groups.values_list('name', flat=True)

        permissions_map = {
            "create": "add_projectsmodel",
            "update": "change_projectsmodel",
            "partial_update": "change_projectsmodel",
            "list": "view_projectsmodel",
            "retrieve": "view_projectsmodel",
            "assign_project": "assign_projectsmodel",
            "destroy": "delete_projectsmodel",
            "add_members": "add_projectmembers",
        }

        required_permission = permissions_map.get(view.action)
        if not required_permission:
            return False
        
        return any(
            required_permission in ROLE_PERMISSIONS.get(group, [])
            for group in user_groups
        )

    def has_object_permission(self, request, view, obj): # type: ignore
        """Object-level permissons for projects
        Creator of the project always has access, or user must have the appropriate permissions"""

        # Project creator has full access
        if obj.created_by == request.user:
            return True
        
        user_groups = request.user.groups.value_list('name', flat=True)

        permissions_map = {
            "list": "view_projectsmodel",
            "retrieve": "view_projectsmodel",
            "update": "change_projectsmodel",
            "partial_update": "change_projectsmodel",
            "assign_project": "assign_projectsmodel",
            "destroy": "delete_projectsmodel",
            "add_members": "add_projectmembers",
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

    def has_permission(self, request, view): # type: ignore
        if not request.user.is_authenticated:
            return False
        
        user_groups = request.user.groups.values_list('name', flat=True)

        permissions_map = {
            "create": "add_taskmodel",
            "update": "change_taskmodel",
            "list": "view_taskmodel",
            "retrieve": "view_taskmodel",
            "destroy": "delete_taskmodel",
            "update_status": "change_taskmodel",
            "update_priority": "change_taskmodel",
            "assign": "change_taskmodel",
        }

        required_permission = permissions_map.get(view.action)
        if not required_permission:
            return False
        
        return any(
            required_permission in ROLE_PERMISSIONS.get(group, [])
            for group in user_groups
        )

    def has_object_permission(self, request, view, obj): # type: ignore
        """Object-level permissons for tasks
        Creator of the task always has access, or user must have the appropriate permissions"""

        # Task creator has full access
        if obj.created_by == request.user:
            return True
        
        user_groups = request.user.groups.value_list('name', flat=True)

        permissions_map = {
            "update": "change_taskmodel",
            "partial_update": "change_taskmodel",
            "retrieve": "view_taskmodel",
            "destroy": "delete_taskmodel",
            "update_status": "change_taskmodel",
            "update_priority": "change_taskmodel",
            "assign": "change_taskmodel",
        }

        required_permissions = permissions_map.get(view.action)
        if not required_permissions:
            return False
        
        return any(
            required_permissions in ROLE_PERMISSIONS.get(group, [])
            for group in user_groups
        )