import requests
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from django.conf import settings
from services.api_client import APIClient
from .forms import ProjectCreationForm
from services.project_service import ProjectService

@login_required
def create_project(request):
    if request.method == "POST":
        form = ProjectCreationForm(request.POST)

        if form.is_valid():

            ProjectService.create_project(
                user = request.user,
                data = form.cleaned_data
            )

            messages.success(request, "Project was created successfully")
    else:
        form = ProjectCreationForm()     
        messages.error(request, "Failed to create the project.")  

    return render(request, 'projects/create_project.html', {'form': form})