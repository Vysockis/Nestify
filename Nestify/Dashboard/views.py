from django.shortcuts import render
from django.utils import timezone
from Nestify.decorators import family_member_required


@family_member_required
def dashboard(request):
    return render(request, 'dashboard/main.html')

def format_time_difference_in(dt1, dt2):

    # Ensure both datetime objects are aware and in the same timezone
    if timezone.is_naive(dt1):
        dt1 = timezone.make_aware(dt1, timezone.get_current_timezone())

    if timezone.is_naive(dt2):
        dt2 = timezone.make_aware(dt2, timezone.get_current_timezone())

    # Calculate difference
    time_diff = dt1 - dt2
    total_seconds = int(abs(time_diff.total_seconds()))  # Ensure positive difference for calculation

    days = total_seconds // 86400  # 86400 seconds in a day
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60

    def lietuviskai(number, word_singular, word_plural_2_9, word_plural_10_plus):
        """ Teisingas linksniavimas pagal skaičių """
        if number == 1:
            return f"{number} {word_singular}"
        elif 2 <= number <= 9:
            return f"{number} {word_plural_2_9}"
        else:
            return f"{number} {word_plural_10_plus}"

    # Determine if it's in the past or future
    prefix = "prieš" if dt1 > dt2 else "po"

    if days > 0:
        return f"{prefix} {lietuviskai(days, 'dieną', 'dienas', 'dienų')}"
    elif hours > 0:
        return f"{prefix} {lietuviskai(hours, 'valandą', 'valandas', 'valandų')}"
    elif minutes > 0:
        return f"{prefix} {lietuviskai(minutes, 'minutes', 'minučių', 'minučių')}"
    else:
        return "ką tik"
