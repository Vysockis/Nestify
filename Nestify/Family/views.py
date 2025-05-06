from django.http import JsonResponse
from Nestify.decorators import family_member_required
from django.shortcuts import render, redirect
import json
from . import models  # Import from local models
import stripe
from django.conf import settings
import time
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages

stripe.api_key = settings.STRIPE_SECRET_KEY

# Create your views here.


@family_member_required
def members(request):
    """API endpoint to fetch family list and items."""
    user = request.user
    family_members = user.getFamily().get_family_members()

    members = []
    for member in family_members:
        members.append({
            "id": member.pk,
            "name": member.user.first_name,
            "surname": member.user.last_name,
            "kid": member.kid,
            "admin": member.admin,
            "current": True if member.user == user else False
        })

    return JsonResponse({"family_members": members}, safe=False)


@family_member_required
def family_settings(request):
    if not request.user.getFamily().creator == request.user:
        return JsonResponse(
            {"error": "Only family admin can access settings"}, status=403)

    family = request.user.getFamily()
    settings = models.FamilySettings.get_or_create_settings(family)

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            settings.inventory_notifications = data.get(
                'inventory_notifications', settings.inventory_notifications)
            settings.task_notifications = data.get(
                'task_notifications', settings.task_notifications)
            settings.finance_notifications = data.get(
                'finance_notifications', settings.finance_notifications)
            settings.save()
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return render(request, 'family/settings.html', {
        'settings': settings,
        'notification_choices': models.FamilySettings.NOTIFICATION_RECIPIENTS
    })


@family_member_required
def manage(request):
    user = request.user
    family = user.getFamily()
    is_admin = family.creator == user
    members = family.get_family_members()
    pending_members = family.get_pending_members() if is_admin else []
    invitation_codes = models.FamilyCode.objects.filter(
        family=family, used=False) if is_admin else []

    # Always create settings for admin
    if is_admin:
        settings = models.FamilySettings.get_or_create_settings(family)
    else:
        settings = None

    context = {
        'is_admin': is_admin,
        'members': members,
        'pending_members': pending_members,
        'invitation_codes': invitation_codes,
        'settings': settings,
    }

    return render(request, 'family/manage.html', context)


@family_member_required
def settings_api(request):
    if not request.user.getFamily().creator == request.user:
        return JsonResponse(
            {"error": "Only family admin can access settings"}, status=403)

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            family = request.user.getFamily()
            settings = models.FamilySettings.get_or_create_settings(family)
            settings.inventory_notifications = data.get(
                'inventory_notifications', settings.inventory_notifications)
            settings.task_notifications = data.get(
                'task_notifications', settings.task_notifications)
            settings.save()
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=400)


def create_stripe_session(request, family_id):
    try:
        family = models.Family.objects.get(id=family_id)
        if family.is_paid:
            return redirect('family_manage')

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': f'Family Plan - {family.name}',
                    },
                    'unit_amount': 5000,  # 50 EUR in cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f'{settings.SITE_URL}/family/manage/',
            cancel_url=f'{settings.SITE_URL}/family/manage/',
            metadata={
                'family_id': family.id
            },
            expires_at=int(time.time() + 1800)  # 30 minutes from now
        )

        family.checkout_url = session.url
        family.save()

        return redirect(session.url)
    except models.Family.DoesNotExist:
        return redirect('family_manage')


@family_member_required
def payment_required(request):
    family = request.user.getFamily()
    if family.is_paid:
        return redirect('family_manage')

    return render(request, 'family/payment_required.html', {
        'family': family,
        'checkout_url': family.checkout_url
    })

# Family management views


@login_required
def create_family(request):
    if request.method == 'POST':
        family_name = request.POST.get('family_name')
        if not family_name:
            messages.error(request, 'Šeimos pavadinimas yra privalomas.')
            return redirect('landing')

        try:
            # Check if user already has a family
            if models.FamilyMember.objects.filter(user=request.user).exists():
                messages.error(
                    request, 'Jūs jau priklausote šeimai arba turite aktyvų prašymą.')
                return redirect('landing')

            # Create new family
            family = models.Family.objects.create(
                name=family_name,
                creator=request.user
            )

            # Create family member (creator is automatically admin and
            # accepted)
            models.FamilyMember.objects.create(
                user=request.user,
                family=family,
                admin=True,
                kid=False,
                accepted=True
            )

            # Redirect to create Stripe session
            return redirect('create_stripe_session', family_id=family.id)

        except Exception as e:
            messages.error(request, f'Įvyko klaida kuriant šeimą: {str(e)}')
            return redirect('landing')

    return render(request, 'signup/create_family.html')


@login_required
def join_family(request):
    if request.method == 'POST':
        code = request.POST.get('invitation_code')
        try:
            # Find the invitation code
            family_code = models.FamilyCode.objects.get(code=code)

            # Check if code is already used
            if family_code.used:
                messages.error(
                    request, 'Šis pakvietimo kodas jau buvo panaudotas.')
                return redirect('landing')

            # Check if user is already in a family
            if models.FamilyMember.objects.filter(user=request.user).exists():
                messages.error(
                    request, 'Jūs jau priklausote šeimai arba turite aktyvų prašymą.')
                return redirect('landing')

            # Create family member with accepted=False
            models.FamilyMember.objects.create(
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

            messages.success(
                request,
                'Prašymas prisijungti prie šeimos išsiųstas. Laukite administratoriaus patvirtinimo.')
            return redirect('landing')

        except models.FamilyCode.DoesNotExist:
            messages.error(request, 'Neteisingas pakvietimo kodas.')
            return redirect('landing')
        except Exception:
            messages.error(
                request, 'Įvyko klaida bandant prisijungti prie šeimos.')
            return redirect('landing')

    return render(request, 'signup/family_choice.html')


@login_required
def cancel_join_request(request):
    if request.method == 'POST':
        try:
            # Find and delete the pending request
            family_member = models.FamilyMember.objects.get(
                user=request.user,
                accepted=False
            )

            # Get the family code associated with this request
            family_code = models.FamilyCode.objects.get(
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

            messages.success(
                request, 'Prašymas prisijungti prie šeimos atšauktas.')
        except (models.FamilyMember.DoesNotExist, models.FamilyCode.DoesNotExist):
            messages.error(request, 'Prašymas nerastas.')

    return redirect('landing')


@login_required
@require_http_methods(['POST'])
def generate_invitation_code(request):
    try:
        # Get the family member and check admin status
        family_member = models.FamilyMember.objects.get(
            user=request.user, accepted=True)
        if not family_member.admin:
            return JsonResponse(
                {'error': 'Unauthorized - must be admin'}, status=403)

        # Create new code
        try:
            code = models.FamilyCode.objects.create(
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

    except models.FamilyMember.DoesNotExist:
        return JsonResponse({'error': 'Not a family member'}, status=403)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")  # Server-side logging
        return JsonResponse({'error': 'Server error'}, status=500)


@login_required
@require_http_methods(['DELETE'])
def delete_invitation_code(request, code_id):
    try:
        family_member = models.FamilyMember.objects.get(
            user=request.user, accepted=True)
        if not family_member.admin:
            return JsonResponse({'error': 'Unauthorized'}, status=403)

        try:
            code = models.FamilyCode.objects.get(
                id=code_id, family=family_member.family)
            code.delete()
            return JsonResponse({'status': 'success'})
        except models.FamilyCode.DoesNotExist:
            return JsonResponse({'error': 'Code not found'}, status=404)
    except models.FamilyMember.DoesNotExist:
        return JsonResponse({'error': 'Not a family member'}, status=403)


@login_required
@require_http_methods(['POST'])
def approve_member(request, member_id):
    try:
        # Check if user is admin
        admin_member = models.FamilyMember.objects.get(
            user=request.user, accepted=True, admin=True)

        # Get pending member
        pending_member = models.FamilyMember.objects.get(
            id=member_id,
            family=admin_member.family,
            accepted=False
        )

        # Approve member
        pending_member.accepted = True
        pending_member.save()

        return JsonResponse({'status': 'success'})
    except models.FamilyMember.DoesNotExist:
        return JsonResponse(
            {'error': 'Unauthorized or member not found'}, status=403)


@login_required
@require_http_methods(['DELETE'])
def reject_member(request, member_id):
    try:
        # Check if user is admin
        admin_member = models.FamilyMember.objects.get(
            user=request.user, accepted=True, admin=True)

        # Get pending member
        pending_member = models.FamilyMember.objects.get(
            id=member_id,
            family=admin_member.family,
            accepted=False
        )

        # Delete the pending member
        pending_member.delete()

        return JsonResponse({'status': 'success'})
    except models.FamilyMember.DoesNotExist:
        return JsonResponse(
            {'error': 'Unauthorized or member not found'}, status=403)


@login_required
@require_http_methods(['POST'])
def toggle_kid_status(request, member_id):
    try:
        family_member = models.FamilyMember.objects.get(
            user=request.user, accepted=True)
        if not family_member.admin:
            return JsonResponse({'error': 'Unauthorized'}, status=403)

        try:
            data = json.loads(request.body)
            target_member = models.FamilyMember.objects.get(
                id=member_id, family=family_member.family, accepted=True)

            if target_member.admin:
                return JsonResponse(
                    {'error': 'Cannot modify admin status'}, status=400)

            target_member.kid = data.get('is_kid', False)
            target_member.save()

            return JsonResponse({'status': 'success'})
        except models.FamilyMember.DoesNotExist:
            return JsonResponse({'error': 'Member not found'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except models.FamilyMember.DoesNotExist:
        return JsonResponse({'error': 'Not a family member'}, status=403)


@login_required
@require_http_methods(['DELETE'])
def remove_family_member(request, member_id):
    try:
        family_member = models.FamilyMember.objects.get(
            user=request.user, accepted=True)
        if not family_member.admin:
            return JsonResponse({'error': 'Unauthorized'}, status=403)

        try:
            target_member = models.FamilyMember.objects.get(
                id=member_id, family=family_member.family, accepted=True)

            if target_member.admin:
                return JsonResponse(
                    {'error': 'Cannot remove admin'}, status=400)

            target_member.delete()
            return JsonResponse({'status': 'success'})
        except models.FamilyMember.DoesNotExist:
            return JsonResponse({'error': 'Member not found'}, status=404)
    except models.FamilyMember.DoesNotExist:
        return JsonResponse({'error': 'Not a family member'}, status=403)
