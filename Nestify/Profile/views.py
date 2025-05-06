from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, authenticate, login as auth_login
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from Family import models as fModels
from Profile.forms import CustomUserCreationForm

# Create your views here.


@login_required
def landing(request):
    try:
        # Check if user exists in FamilyMember model
        family_member = fModels.FamilyMember.objects.get(user=request.user)
        if family_member.accepted:
            return redirect('/dashboard')
        else:
            # User has a pending request
            return render(request, 'signup/waiting_approval.html', {
                'family_name': family_member.family.name
            })
    except fModels.FamilyMember.DoesNotExist:
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
                fModels.FamilyMember.objects.get(user=user)
                return redirect(request.POST.get('next', 'landing'))
            except ObjectDoesNotExist:
                # If not a family member, redirect to family choice page
                return redirect('landing')
        return render(request, 'signup/login.html',
                      {'error': 'Neteisingas vartotojo vardas arba slaptažodis'})

    return render(request, 'signup/login.html', {'error': ''})


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request, 'Registracija sėkminga! Galite prisijungti.')
            return redirect('login')
        return render(request, 'signup/register.html',
                      {'form': form, 'error_message': 'Neteisingi duomenys'})

    return render(request, 'signup/register.html',
                  {'form': CustomUserCreationForm()})
