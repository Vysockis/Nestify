from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser as User


class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True, label='Vardas')
    last_name = forms.CharField(max_length=150, required=True, label='Pavardė')
    email = forms.EmailField(required=True, label='El. paštas')
    username = forms.CharField(
        max_length=150,
        required=True,
        label='Vartotojo vardas',
        error_messages={'unique': 'Toks vartotojo vardas jau egzistuoja.'}
    )

    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'password1',
            'password2']
        labels = {
            'password1': 'Slaptažodis',
            'password2': 'Pakartokite slaptažodį'
        }
        error_messages = {
            'password2': {
                'password_mismatch': 'Slaptažodžiai nesutampa.'
            }
        }
