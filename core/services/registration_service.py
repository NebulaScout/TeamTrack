from django.contrib.auth.models import User

from accounts.models import RegisterModel
from .group_assignment import set_user_role
from .enums import RoleEnum

def register_user(username, first_name, last_name, email, password):
    # check if email exists
    if User.objects.filter(email=email).exists():
        raise ValueError("A user with this email already exists")

    user = User.objects.create_user(
        username = username,
        email = email,
        password = password,
        first_name = first_name,
        last_name = last_name,
    )
    set_user_role(user, RoleEnum.GUEST) # Assign default permissions to a new user


    register_model = RegisterModel.objects.create(user = user)

    return register_model