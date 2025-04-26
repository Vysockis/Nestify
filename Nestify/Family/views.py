from django.http import JsonResponse
from Nestify.decorators import family_member_required
from django.shortcuts import render, redirect
import json
from . import models  # Import from local models
import stripe
from django.conf import settings
import time

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
        return JsonResponse({"error": "Only family admin can access settings"}, status=403)

    family = request.user.getFamily()
    settings = models.FamilySettings.get_or_create_settings(family)

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            settings.inventory_notifications = data.get('inventory_notifications', settings.inventory_notifications)
            settings.task_notifications = data.get('task_notifications', settings.task_notifications)
            settings.finance_notifications = data.get('finance_notifications', settings.finance_notifications)
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
    invitation_codes = models.FamilyCode.objects.filter(family=family, used=False) if is_admin else []
    
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
        return JsonResponse({"error": "Only family admin can access settings"}, status=403)

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            family = request.user.getFamily()
            settings = models.FamilySettings.get_or_create_settings(family)
            settings.inventory_notifications = data.get('inventory_notifications', settings.inventory_notifications)
            settings.task_notifications = data.get('task_notifications', settings.task_notifications)
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
