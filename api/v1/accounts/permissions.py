from rest_framework import permissions


class UserPermissions(permissions.BasePermission):
    """Override default permissions"""
    def has_permission(self, request, view): # type: ignore
        if view.action == 'list': # Only admin can view all users
            return bool(request.user.is_authenticated and request.user.is_staff)
        elif view.action == 'create': # Any user can register
            return True
        elif view.action in ['retrieve', 'update', 'partial_update']: # Only authenticated users can modify data
            return bool(request.user.is_authenticated)
        elif view.action == 'destroy': # Only admin can delete data
            return bool(request.user.is_authenticated and request.user.is_staff)
        else:
            return False

    def has_object_permission(self, request, view, obj):
        """ Ensures that a user can only access or modify a 
        specific object if they own it or have administrative privileges,
          preventing unauthorized access to other users': data."""
        return request.user == obj or request.user.is_staff
