from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from Nestify.decorators import family_member_required
from List import models as lModels
from Plan import models as pModels
from Family.models import Notification


@family_member_required
def dashboard(request):
    family = request.user.getFamily()
    notifications = Notification.objects.filter(
        family=family,
        recipient=request.user,
        is_read=False
    ).order_by('-created_at')[:5]

    context = {
        'notifications': notifications,
        'unread_count': notifications.count()
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
        plan__isnull=True
    ).exclude(list_type='FINANCE')
    
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
