from django import forms

from .models import ProjectsModel

class ProjectCreationForm(forms.ModelForm):
    class Meta:
        model = ProjectsModel
        fields = ["project_name", "description", "start_date", "end_date"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }

    