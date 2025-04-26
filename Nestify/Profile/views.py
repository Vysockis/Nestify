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
        is_admin = family_member.admin
        family = family_member.family
    except fModels.FamilyMember.DoesNotExist:
        messages.error(request, 'Jūs nesate šeimos narys.')
        return redirect('landing')
    
    context = {
        'is_admin': is_admin,
        'members': fModels.FamilyMember.objects.filter(family=family, accepted=True),
        'pending_members': fModels.FamilyMember.objects.filter(family=family, accepted=False) if is_admin else None,
        'invitation_codes': fModels.FamilyCode.objects.filter(family=family, used=False) if is_admin else None
    }
    
    return render(request, 'family/manage.html', context)

@login_required
@require_http_methods(['POST'])
def approve_member(request, member_id):
    try:
        # Check if user is admin
        admin_member = fModels.FamilyMember.objects.get(user=request.user, accepted=True, admin=True)
        
        # Get pending member
        pending_member = fModels.FamilyMember.objects.get(
            id=member_id,
            family=admin_member.family,
            accepted=False
        )
        
        # Approve member
        pending_member.accepted = True
        pending_member.save()
        
        return JsonResponse({'status': 'success'})
    except fModels.FamilyMember.DoesNotExist:
        return JsonResponse({'error': 'Unauthorized or member not found'}, status=403)

@login_required
@require_http_methods(['DELETE'])
def reject_member(request, member_id):
    try:
        # Check if user is admin
        admin_member = fModels.FamilyMember.objects.get(user=request.user, accepted=True, admin=True)
        
        # Get pending member
        pending_member = fModels.FamilyMember.objects.get(
            id=member_id,
            family=admin_member.family,
            accepted=False
        )
        
        # Delete the pending member
        pending_member.delete()
        
        return JsonResponse({'status': 'success'})
    except fModels.FamilyMember.DoesNotExist:
        return JsonResponse({'error': 'Unauthorized or member not found'}, status=403)

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

@login_required
def join_family(request):
    if request.method == 'POST':
        code = request.POST.get('invitation_code')
        try:
            # Find the invitation code
            family_code = fModels.FamilyCode.objects.get(code=code)
            
            # Check if code is already used
            if family_code.used:
                messages.error(request, 'Šis pakvietimo kodas jau buvo panaudotas.')
                return redirect('landing')
            
            # Check if user is already in a family
            if fModels.FamilyMember.objects.filter(user=request.user).exists():
                messages.error(request, 'Jūs jau priklausote šeimai arba turite aktyvų prašymą.')
                return redirect('landing')
            
            # Create family member with accepted=False
            fModels.FamilyMember.objects.create(
                user=request.user,
                family=family_code.family,
                admin=False,
                kid=False,
                accepted=False
            )
            
            # Mark code as used
            family_code.used = True
            family_code.user = request.user
            family_code.save()
            
            messages.success(request, 'Prašymas prisijungti prie šeimos išsiųstas. Laukite administratoriaus patvirtinimo.')
            return redirect('landing')
            
        except fModels.FamilyCode.DoesNotExist:
            messages.error(request, 'Neteisingas pakvietimo kodas.')
            return redirect('landing')
        except Exception:
            messages.error(request, 'Įvyko klaida bandant prisijungti prie šeimos.')
            return redirect('landing')
    
    return render(request, 'signup/family_choice.html')

@login_required
def cancel_join_request(request):
    if request.method == 'POST':
        try:
            # Find and delete the pending request
            family_member = fModels.FamilyMember.objects.get(
                user=request.user,
                accepted=False
            )
            
            # Get the family code associated with this request
            family_code = fModels.FamilyCode.objects.get(
                user=request.user,
                family=family_member.family,
                used=True
            )
            
            # Delete the family member request
            family_member.delete()
            
            # Mark the code as unused so it can be used again
            family_code.used = False
            family_code.user = None
            family_code.save()
            
            messages.success(request, 'Prašymas prisijungti prie šeimos atšauktas.')
        except (fModels.FamilyMember.DoesNotExist, fModels.FamilyCode.DoesNotExist):
            messages.error(request, 'Prašymas nerastas.')
            
    return redirect('landing')

@login_required
def create_family(request):
    if request.method == 'POST':
        family_name = request.POST.get('family_name')
        if not family_name:
            messages.error(request, 'Šeimos pavadinimas yra privalomas.')
            return redirect('landing')

        try:
            # Check if user already has a family
            if fModels.FamilyMember.objects.filter(user=request.user).exists():
                messages.error(request, 'Jūs jau priklausote šeimai arba turite aktyvų prašymą.')
                return redirect('landing')

            # Create new family
            family = fModels.Family.objects.create(
                name=family_name,
                creator=request.user
            )

            # Create family member (creator is automatically admin and accepted)
            fModels.FamilyMember.objects.create(
                user=request.user,
                family=family,
                admin=True,
                kid=False,
                accepted=True
            )

            # Redirect to create Stripe session
            return redirect('create_stripe_session', family_id=family.id)

            messages.success(request, f'Šeima "{family_name}" sėkmingai sukurta!')
            return redirect('payment_required')

        except Exception as e:
            messages.error(request, f'Įvyko klaida kuriant šeimą: {str(e)}')
            return redirect('landing')

    return render(request, 'signup/create_family.html')
