from django.contrib.auth.models import Group

def set_user_role(user, role_name: str):
    try:
        group = Group.objects.get(name = role_name)
    except Group.DoesNotExist:
        raise RuntimeError(f"Role {role_name} doesn't exist")
    
    user.groups.set([group])