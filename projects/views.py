import requests
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from django.conf import settings
from services.api_client import APIClient
from .forms import ProjectCreationForm

@login_required
def create_project(request):
    if request.method == "POST":
        form = ProjectCreationForm(request.POST)

        if form.is_valid():
            data = {
                "project_name": form.cleaned_data['project_name'],
                "description":  form.cleaned_data['description'],
                "start_date":  form.cleaned_data['start_date'].isoformat(),
                "end_date":  form.cleaned_data['end_date'].isoformat(),
            }

            api = APIClient(request)

            try:
                response = api.post("/api/v1/projects/", json=data)

                if response.status_code == 201:
                    messages.success(request, "Project was created successfully")
                else:
                    messages.error(request, f"Failed to create project: {response.text}")

            except requests.exceptions.HTTPError as e:
                messages.error(request, f"HTTP error occurred: {e}")
            except requests.exceptions.RequestException as e:
                messages.error(request, f"Connection error: {e}")
    else:
        form = ProjectCreationForm()       

    return render(request, 'projects/create_project.html', {'form': form})