from django import forms
from django.contrib.auth.models import User

# from .models import RegisterModel

class RegistrationForm(forms.Form):
    username = forms.CharField(max_length=100)
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    email = forms.EmailField(max_length=100)
    # role = forms.ChoiceField(
    #     choices=RegisterModel.RoleEnum.choices,
    #     widget=forms.RadioSelect
    # )
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)    

    def clean(self):
        cleaned_data = super().clean()
        passwd = cleaned_data.get('password')
        confirm_passwd = cleaned_data.get("confirm_password")

        if passwd and confirm_passwd and passwd != confirm_passwd:
            self.add_error(confirm_passwd, "Passwords do not match")
        
        return cleaned_data