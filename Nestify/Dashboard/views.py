from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from Nestify.decorators import family_member_required
from List import models as lModels
from Plan import models as pModels
from Family.models import Notification
from .models import SmartDevice


@family_member_required
def dashboard(request):
    family = request.user.getFamily()
    notifications = Notification.objects.filter(
        family=family,
        recipient=request.user,
        is_read=False
    ).order_by('-created_at')[:5]

    # Get smart devices for the family
    smart_devices = SmartDevice.objects.filter(family=family)

    context = {
        'notifications': notifications,
        'unread_count': notifications.count(),
        'smart_devices': smart_devices
    }
    
    return render(request, 'dashboard/main.html', context)


@family_member_required
def mark_notification_read(request, notification_id):
    try:
        notification = Notification.objects.get(
            id=notification_id,
            recipient=request.user,
            is_read=False
        )
        notification.is_read = True
        notification.save()
        return JsonResponse({'status': 'success'})
    except Notification.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Notification not found'}, status=404)


@family_member_required
def calendar(request):
    return render(request, 'calendar/main.html')

def format_time_difference_in(dt1, dt2):
    if timezone.is_naive(dt1):
        dt1 = timezone.make_aware(dt1, timezone.get_current_timezone())
    if timezone.is_naive(dt2):
        dt2 = timezone.make_aware(dt2, timezone.get_current_timezone())

    time_diff = dt1 - dt2
    total_seconds = int(abs(time_diff.total_seconds()))

    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60

    def lietuviskai(number, word_singular, word_plural_2_9, word_plural_10_plus):
        if number == 1:
            return f"{number} {word_singular}"
        elif 2 <= number <= 9:
            return f"{number} {word_plural_2_9}"
        return f"{number} {word_plural_10_plus}"

    prefix = "prieš" if dt1 > dt2 else "po"

    if days > 0:
        return f"{prefix} {lietuviskai(days, 'dieną', 'dienas', 'dienų')}"
    elif hours > 0:
        return f"{prefix} {lietuviskai(hours, 'valandą', 'valandas', 'valandų')}"
    elif minutes > 0:
        return f"{prefix} {lietuviskai(minutes, 'minutes', 'minučių', 'minučių')}"
    return "ką tik"

@family_member_required
def calendar_events(request):
    family = request.user.getFamily()

    list_events = lModels.List.objects.filter(
        family=family,
        plan__isnull=True,
        datetime__isnull=False
    ).exclude(list_type__in=['FINANCE', 'MEAL'])
    
    list_event_list = [{
        "id": event.id,
        "title": event.name,
        "start": event.datetime.isoformat(),
        "end": None,
    } for event in list_events]

    plan_events = pModels.Plan.objects.filter(family=family)
    plan_event_list = [{
        "id": event.id,
        "title": event.name,
        "start": event.datetime.isoformat(),
        "end": None,
        "url": f"{request.build_absolute_uri(reverse('plan-view'))}?planId={event.id}"
    } for event in plan_events]

    return JsonResponse(list_event_list + plan_event_list, safe=False)

@family_member_required
def smart_dashboard(request):
    family = request.user.getFamily()
    devices = SmartDevice.objects.filter(family=family)
    context = {
        'devices': devices,
    }
    return render(request, 'dashboard/smart.html', context)

@family_member_required
def toggle_device(request, device_id):
    device = get_object_or_404(SmartDevice, id=device_id, family=request.user.getFamily())
    device.is_on = not device.is_on
    device.save()
    return JsonResponse({
        'status': 'success',
        'is_on': device.is_on
    })

@family_member_required
def update_brightness(request, device_id):
    device = get_object_or_404(SmartDevice, id=device_id, family=request.user.getFamily())
    brightness = int(request.POST.get('brightness', 100))
    brightness = max(0, min(100, brightness))  # Ensure brightness is between 0 and 100
    device.brightness = brightness
    device.save()
    return JsonResponse({
        'status': 'success',
        'brightness': device.brightness
    })

@family_member_required
def add_device(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

    name = request.POST.get('name')
    room = request.POST.get('room')
    device_type = request.POST.get('device_type')

    if not all([name, room, device_type]):
        return JsonResponse({'status': 'error', 'message': 'Missing required fields'}, status=400)

    try:
        device = SmartDevice.objects.create(
            name=name,
            room=room,
            device_type=device_type,
            family=request.user.getFamily(),
            is_on=False,
            brightness=100
        )
        return JsonResponse({
            'status': 'success',
            'device': {
                'id': device.id,
                'name': device.name,
                'room': device.room,
                'type': device.device_type
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@family_member_required
def delete_device(request, device_id):
    device = get_object_or_404(SmartDevice, id=device_id, family=request.user.getFamily())
    device.delete()
    return JsonResponse({
        'status': 'success',
        'message': 'Device deleted successfully'
    })
