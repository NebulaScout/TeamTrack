from django.contrib.auth.models import User
from ..models import RegisterModel

def register_user(username, first_name, last_name, email, password):
    user = User.objects.create_user(
        username = username,
        email = email,
        password = password,
        first_name = first_name,
        last_name = last_name,
    )

    register_model = RegisterModel.objects.create(user = user)

    return register_model