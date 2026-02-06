from django.contrib.auth.models import Group

from .enums import RoleEnum

def set_user_role(user, role_name: RoleEnum):
    try:
        group = Group.objects.get(name = role_name.value)
    except Group.DoesNotExist:
        raise RuntimeError(f"Role {role_name.value} doesn't exist")
    
    user.groups.set([group])