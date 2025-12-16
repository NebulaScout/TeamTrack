from django.contrib.auth.models import Group, Permission

ROLE_PERMISSIONS = {
    "Admin": [
        # project_model_permissions
       "add_projectsmodel",
        "change_projectsmodel",
        "view_projectsmodel",
        "assign_project",
        "delete_projectsmodel",
        # user_permissions
        "change_user",
        "delete_user",
        "view_user",
    ],
    "Project Manager": [
        # project_model_permissions
        "add_projectsmodel",
        "change_projectsmodel",
        "view_projectsmodel",
        "assign_project",
        "delete_projectsmodel",
        # user_permissions
        "view_user",
    ],
    "Developer": [
        # project_model_permissions
        "view_projectsmodel",
        # user_permissions
        "view_user",
        
    ],
    "Guest": [
        # project_model_permissions
        "view_projectsmodel",
    ],
}

def initialize_roles():
    for role_name, perm_codenames in ROLE_PERMISSIONS.items():
        group, _ = Group.objects.get_or_create(name=role_name)

        permissions = Permission.objects.filter(
            codename__in = perm_codenames
        )

        group.permissions.set(permissions)