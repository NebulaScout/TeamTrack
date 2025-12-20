from django.contrib.auth.models import Group, Permission

ROLE_PERMISSIONS = {
    "Admin": [
        # project_model_permissions
        "add_projectsmodel",
        "change_projectsmodel",
        "view_projectsmodel",
        # "assign_role",
        "delete_projectsmodel",
        "add_projectmembers",
        # user_permissions
        "change_user",
        "delete_user",
        "view_user",
        # member assignment
        "add_projectmembers",
        "delete_projectmembers",
        "change_projectmembers",
        "view_projectmembers",  
        # task permissions  
        "add_taskmodel",
        "view_taskmodel",
        "change_taskmodel",
        "delete_taskmodel",
    ],
    "Project Manager": [
        # project_model_permissions
        "add_projectsmodel",
        "change_projectsmodel",
        "view_projectsmodel",
        # "assign_projectsmodels",
        "delete_projectsmodel",
        "add_projectmembers",
        # user_permissions
        "view_user",
        # member assignment
        "add_projectmembers",
        "delete_projectmembers",
        "change_projectmembers",
        "view_projectmembers",
        # task permissions  
        "add_taskmodel",
        "view_taskmodel",
        "change_taskmodel",
        "delete_taskmodel",
    ],
    "Developer": [
        # project_model_permissions
        "view_projectsmodel",
        # user_permissions
        "view_user",
        # member assignment
        "view_projectmembers",
        # task permissions  
        "view_taskmodel",
        "change_taskmodel",
    ],
    "Guest": [
        # project_model_permissions
        "view_projectsmodel",
        # member assignment
        "view_projectmembers",
        # task permissions  
        "view_taskmodel",
    ],
}

def initialize_roles():
    for role_name, perm_codenames in ROLE_PERMISSIONS.items():
        group, _ = Group.objects.get_or_create(name=role_name)

        permissions = Permission.objects.filter(
            codename__in = perm_codenames
        )

        found = set(permissions.values_list("codename", flat=True))  # Check for available permissions
        missing = set(perm_codenames) - found # Chaeck for missing permissions

        # Check if a role is missing and fail loudly if true
        if missing:
            raise RuntimeError(f"Missing permissions for {role_name}: {missing}")

        group.permissions.set(permissions)