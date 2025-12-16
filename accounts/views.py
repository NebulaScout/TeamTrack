import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import requires_csrf_token, csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import AuthenticationForm
from django.conf import settings
from django.contrib.auth import logout
from rest_framework_simplejwt.tokens import RefreshToken


from .forms import RegistrationForm
from services.api_client import APIClient

class CustomLoginView(LoginView):
    """Override the django LoginView class to generate JWT tokens"""

    template_name = 'accounts/login.html'
    form_class = AuthenticationForm

    def form_valid(self, form):
        # Get username and passwod from the form
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")

        api_url = f"{settings.BASE_URL}/api/token/" # Token generation endpoint
        data = {"username": username, "password": password}

        try:
            r = requests.post(api_url, json=data)
            r.raise_for_status()

            token_data = r.json()
            print(f"Token created: {token_data}")
            # Store tokens in session
            self.request.session['access_token'] = token_data.get('access')
            self.request.session['refresh_token'] = token_data.get('refresh')

        except requests.exceptions.HTTPError as e:
            messages.error(self.request, "Failed to generate authentication token")
        except requests.exceptions.RequestException as e:
            messages.error(self.request, f"Connection error: {e}")

        return super().form_valid(form)



def register(request):
    """Regeister users"""
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
            api_url = f"{settings.BASE_URL}/api/v1/accounts/register/"

            r = requests.post(api_url, json=data)

            if r.status_code == 201:
                messages.success(request, "Account was created successfully")
                return redirect('login')
            else:
                messages.error(request, f"Registration failed: {r.text}")
    else:
        form = RegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})

def home(request):
    return render(request, 'base.html')

@login_required
def user_profile(request):
    """Retrieve user profile info"""
    api = APIClient(request)

    try:
        response = api.get("/api/v1/accounts/users/")

        if response.status_code == 401:
            messages.error(request, "Session expired. Please log in again.")
            return redirect("login")

        response.raise_for_status()
        user_data = response.json()
        print(f"User data: {user_data}")
        return render(request, 'accounts/user_profile.html', {'user_data': user_data})

    except requests.exceptions.HTTPError as e:
        messages.error(request, f"HTTP error occurred: {e}")
    except requests.exceptions.RequestException as e:
        messages.error(request, f"Connection error: {e}")

    return render(request, 'accounts/user_profile.html')

@login_required
def logout_view(request):
    print(f"Session data: {dict(request.session.items())}")
    # Blacklist JWT tokens
    refresh_token = request.session.get('refresh_token')
    print(f"Refresh token retrieved: {refresh_token}")

    if refresh_token: # check if they exist
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            print("Token blacklisted successfully")
        except Exception as e:
            print(f"Error blacklisting token: {type(e).__name__}: {e}")


    # Clear django session
    logout(request)
    print("Django logout called")




    

    return  redirect('login')
        

