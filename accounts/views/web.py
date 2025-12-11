from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import requires_csrf_token, csrf_exempt

from ..models import RegisterModel
from ..forms import RegistrationForm

@csrf_exempt
def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()
            # Create RegisterModel instance with the role
            RegisterModel.objects.create(
                user=user,
                role=form.cleaned_data['role']
            )
            messages.success(request, "Account was created successfully")
            return redirect('home')
    else:
        form = RegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})

def home(request):
    return render(request, 'base.html')