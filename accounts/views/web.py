import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import requires_csrf_token, csrf_exempt

from ..models import RegisterModel
from ..forms import RegistrationForm
from ..services.registration_service import register_user

@csrf_exempt
def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
           
            data = {
                "user": {
                    "username": form.cleaned_data['username'],
                    "first_name": form.cleaned_data['first_name'],
                    "last_name": form.cleaned_data['last_name'],
                    "email": form.cleaned_data['email'],
                    "password": form.cleaned_data['password'],
                    "confirm_password": form.cleaned_data['confirm_password']
                }
            }
            api_url = f"{request.scheme}://{request.get_host()}/accounts/api/register/"

            r = requests.post(api_url, json=data)

            if r.status_code == 201:
                messages.success(request, "Account was created successfully")
                return redirect('home')
            else:
                messages.error(request, f"Registration failed: {r.text}")
    else:
        form = RegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})

def home(request):
    return render(request, 'base.html')