from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth import authenticate, login as auth_login
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages

from Profile.forms import CustomUserCreationForm
from Family import models as fModels

# Create your views here.
@login_required
def landing(request):
    try:
        # Check if user exists in FamilyMember model
        fModels.FamilyMember.objects.get(user=request.user, accepted=True)
        return redirect('/dashboard')
    except ObjectDoesNotExist:
        return render(request, 'signup/family_choice.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            try:
                # Check if user is a member of a family
                fModels.FamilyMember.objects.get(user=user, accepted=True)
                next_url = request.POST.get('next', 'landing')
                return redirect(next_url)
            except ObjectDoesNotExist:
                # If not a family member, redirect to family choice page
                return redirect('landing')
        else:
            return render(request, 'signup/login.html', {'error': 'Invalid username or password'})
    else:
        return render(request, 'signup/login.html', {'error': ''})

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Registracija sėkminga! Galite prisijungti.')
                return redirect('login')
            except Exception as e:
                # Handle other exceptions
                return render(request, 'signup/register.html', {'form': form, 'error_message': str(e)})
    else:
        form = CustomUserCreationForm()

    return render(request, 'signup/register.html', {'form': form})
