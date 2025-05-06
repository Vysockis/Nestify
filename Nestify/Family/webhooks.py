import stripe
from django.http import HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from .models import Family

stripe.api_key = settings.STRIPE_SECRET_KEY


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        family_id = session.get('metadata', {}).get('family_id')
        if family_id:
            try:
                family = Family.objects.get(id=family_id)
                family.is_paid = True
                family.save()
            except Family.DoesNotExist:
                pass

    elif event['type'] == 'checkout.session.expired':
        session = event['data']['object']
        family_id = session.get('metadata', {}).get('family_id')
        if family_id:
            try:
                family = Family.objects.get(id=family_id)
                if not family.is_paid:
                    family.delete()
            except Family.DoesNotExist:
                pass

    return HttpResponse(status=200)
