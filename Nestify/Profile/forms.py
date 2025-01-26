from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser as User

class CustomUserCreationForm(UserCreationForm):
    registration_code = forms.CharField(max_length=100, required=True, help_text='Enter your registration code.')

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'registration_code']
