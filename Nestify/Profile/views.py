from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth import authenticate, login as auth_login
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
from Family import models as fModels

from Profile.forms import CustomUserCreationForm

# Create your views here.
@login_required
def landing(request):
    try:
        # Check if user exists in FamilyMember model
        fModels.FamilyMember.objects.get(user=request.user)
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
                fModels.FamilyMember.objects.get(user=user)
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

@login_required
def manage_family(request):
    try:
        # Check if user exists in FamilyMember model
        family_member = fModels.FamilyMember.objects.get(user=request.user, accepted=True)
        is_admin = family_member.admin  # Note: field is 'admin' not 'is_admin'
        family = family_member.family
    except fModels.FamilyMember.DoesNotExist:
        messages.error(request, 'Jūs nesate šeimos narys.')
        return redirect('landing')
    
    context = {
        'is_admin': is_admin,
        'members': fModels.FamilyMember.objects.filter(family=family, accepted=True),
        'invitation_codes': fModels.FamilyCode.objects.filter(family=family, used=False) if is_admin else None
    }
    
    return render(request, 'family/manage.html', context)

@login_required
@require_http_methods(['POST'])
def generate_invitation_code(request):
    try:
        # Get the family member and check admin status
        family_member = fModels.FamilyMember.objects.get(user=request.user, accepted=True)
        if not family_member.admin:
            return JsonResponse({'error': 'Unauthorized - must be admin'}, status=403)
        
        # Create new code
        try:
            code = fModels.FamilyCode.objects.create(
                family=family_member.family,
                user=None  # Leave user empty until code is used
            )
            
            return JsonResponse({
                'id': code.id,
                'code': code.code
            })
        except Exception as e:
            print(f"Error creating code: {str(e)}")  # Server-side logging
            return JsonResponse({'error': 'Failed to create code'}, status=500)
            
    except fModels.FamilyMember.DoesNotExist:
        return JsonResponse({'error': 'Not a family member'}, status=403)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")  # Server-side logging
        return JsonResponse({'error': 'Server error'}, status=500)

@login_required
@require_http_methods(['DELETE'])
def delete_invitation_code(request, code_id):
    try:
        family_member = fModels.FamilyMember.objects.get(user=request.user, accepted=True)
        if not family_member.admin:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        try:
            code = fModels.FamilyCode.objects.get(id=code_id, family=family_member.family)
            code.delete()
            return JsonResponse({'status': 'success'})
        except fModels.FamilyCode.DoesNotExist:
            return JsonResponse({'error': 'Code not found'}, status=404)
    except fModels.FamilyMember.DoesNotExist:
        return JsonResponse({'error': 'Not a family member'}, status=403)

@login_required
@require_http_methods(['POST'])
def toggle_kid_status(request, member_id):
    try:
        family_member = fModels.FamilyMember.objects.get(user=request.user, accepted=True)
        if not family_member.admin:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        try:
            data = json.loads(request.body)
            target_member = fModels.FamilyMember.objects.get(id=member_id, family=family_member.family, accepted=True)
            
            if target_member.admin:
                return JsonResponse({'error': 'Cannot modify admin status'}, status=400)
            
            target_member.kid = data.get('is_kid', False)
            target_member.save()
            
            return JsonResponse({'status': 'success'})
        except fModels.FamilyMember.DoesNotExist:
            return JsonResponse({'error': 'Member not found'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except fModels.FamilyMember.DoesNotExist:
        return JsonResponse({'error': 'Not a family member'}, status=403)

@login_required
@require_http_methods(['DELETE'])
def remove_family_member(request, member_id):
    try:
        family_member = fModels.FamilyMember.objects.get(user=request.user, accepted=True)
        if not family_member.admin:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        try:
            target_member = fModels.FamilyMember.objects.get(id=member_id, family=family_member.family, accepted=True)
            
            if target_member.admin:
                return JsonResponse({'error': 'Cannot remove admin'}, status=400)
            
            target_member.delete()
            return JsonResponse({'status': 'success'})
        except fModels.FamilyMember.DoesNotExist:
            return JsonResponse({'error': 'Member not found'}, status=404)
    except fModels.FamilyMember.DoesNotExist:
        return JsonResponse({'error': 'Not a family member'}, status=403)
