from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth import authenticate, login as auth_login

from Profile.forms import CustomUserCreationForm

# Create your views here.
def landing(request):
    if request.user.is_authenticated:
        return render(request, 'dashboard/main.html')  # Redirect authenticated users to a dashboard or home page
    return render(request, 'home.html')

@login_required
def logout_view(request):
    logout(request)

    return redirect('landing')

def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            next_url = request.POST.get('next', 'landing')
            return redirect(next_url)
        else:
            return render(request, 'signup/login.html', {'error': 'Invalid username or password'})
    else:
        return render(request, 'signup/login.html', {'error': ''})

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Validate the registration code
            try:
                # Proceed with user creation, authentication, and Stripe customer creation
                user = form.save()
                username = form.cleaned_data.get('username')
                raw_password = form.cleaned_data.get('password1')

                # Authenticate and login the user
                user = authenticate(username=username, password=raw_password)
                auth_login(request, user)
            except Exception as e:
                # Handle other exceptions
                return render(request, 'signup/register.html', {'form': form, 'error_message': str(e)})
    else:
        form = CustomUserCreationForm()

    return render(request, 'signup/register.html', {'form': form})
