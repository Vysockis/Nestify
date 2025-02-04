from django.shortcuts import render
from Nestify.decorators import family_member_required
from django.utils import timezone

from List import models as lModels

@family_member_required
def dashboard(request):
    user = request.user
    list = getList(user)
    return render(request, 'dashboard/main.html', {"family_list": list})  # Redirect authenticated users to a dashboard or home page

def getList(user):
    """Fetch family lists and items."""
    family = user.getFamily()

    if not family:
        return None  # No family found, return None

    # Fetch family lists
    family_lists = lModels.List.get_family_list(family)

    # Convert lists into a dictionary
    now = timezone.now()
    lists_data = []
    for lst in family_lists:
        items = lModels.ListItem.get_list_items(lst)
        list_data = {
            "id": lst.id,
            "name": lst.name,
            "description": lst.description,
            "date": format_time_difference_in(lst.datetime, now),
            "items": [{"id": item.id, "name": item.name, "qty": item.qty if item.qty is not None else 0, "completed": item.completed} for item in items]
        }
        lists_data.append(list_data)

    print(list_data)
    return lists_data  # Return structured data


def format_time_difference_in(datetime, datetime_other):
    """
    Grąžina laiko skirtumą tarp dviejų datetime objektų lietuviškai.
    Palaiko tiek praeities, tiek ateities laikus.
    """
    time_diff = datetime - datetime_other
    days = time_diff.days
    seconds = abs(time_diff.seconds)  # Visada teigiamas skaičius skaičiavimui
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    def lietuviskai(number, word_singular, word_plural_2_9, word_plural_10_plus):
        """ Teisingas linksniavimas pagal skaičių """
        if number == 1:
            return f"{number} {word_singular}"
        elif 2 <= number <= 9:
            return f"{number} {word_plural_2_9}"
        else:
            return f"{number} {word_plural_10_plus}"

    # Nustatyti, ar laikas yra praeityje, ar ateityje
    if days > 0:
        return f"prieš {lietuviskai(days, 'dieną', 'dienas', 'dienų')}"
    elif days < 0:
        return f"po {lietuviskai(abs(days), 'dienos', 'dienų', 'dienų')}"
    elif hours > 0:
        return f"prieš {lietuviskai(hours, 'valandą', 'valandas', 'valandų')}"
    elif hours < 0:
        return f"po {lietuviskai(abs(hours), 'valandos', 'valandų', 'valandų')}"
    elif minutes > 0:
        return f"prieš {lietuviskai(minutes, 'minutę', 'minutes', 'minučių')}"
    elif minutes < 0:
        return f"po {lietuviskai(abs(minutes), 'minutės', 'minučių', 'minučių')}"
    else:
        return "ką tik"
