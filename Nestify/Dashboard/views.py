import json
from django.http import JsonResponse
from django.shortcuts import render
from List.enum import ListType
from Family.models import FamilyMember
from Nestify.decorators import family_member_required
from django.utils import timezone
from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist

from List import models as lModels

@family_member_required
def dashboard(request):
    return render(request, 'dashboard/main.html')  # Redirect authenticated users to a dashboard or home page

@family_member_required
def get_family_list(request):
    """API endpoint to fetch family list and items."""
    user = request.user
    family = user.getFamily()

    if not family:
        return JsonResponse({"error": "No family found"}, status=400)

    # Fetch lists belonging to the family
    family_lists = lModels.List.get_family_list(family)
    family_lists = family_lists.order_by("-datetime")

    # Convert lists and items to JSON format
    data = []
    for lst in family_lists:
        items = lModels.ListItem.get_list_items(lst)  # Fetch items for each list

        itemData = []
        for item in items:
            name = ""
            match lst.list_type:
                case ListType.GROCERY.name:
                    name = f"{item.qty if item.qty is not None else 0}x {item.name}"
                case ListType.TASK.name:
                    user_text = f"{item.assigned_to.first_name}: " if item.assigned_to is not None else ""
                    name = f"{user_text}{item.name}"
                case ListType.MEAL.name:
                    name = f"{item.qty if item.qty is not None else 0}x {item.name}"
                case ListType.OTHER.name:
                    name = f"{item.name}"

            itemData.append({
                "id": item.pk,
                "name": name,
                "completed": item.completed
            })

        data.append({
            "id": lst.id,
            "type": lst.list_type,
            "name": lst.name,
            "date": format_time_difference_in(lst.datetime, timezone.now()),
            "items": itemData
        })

    return JsonResponse({"family_list": data}, safe=False)


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

@family_member_required
def update_item_status(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            item_id = data.get("item_id")
            completed = data.get("completed")

            item = lModels.ListItem.objects.get(pk=item_id)
            item.completed = completed
            item.save()

            return JsonResponse({"success": True, "message": "Sekmingai atnaujinti duomenys"})
        except ObjectDoesNotExist:
            return JsonResponse({"error": "Įrašas nerastas"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Netinkamas kvietimas"}, status=400)

@family_member_required
def item(request):
    if request.method == "DELETE":
        try:
            data = json.loads(request.body)
            item_id = data.get("item_id")

            # Check if the list exists
            list_item = lModels.ListItem.objects.get(pk=item_id)
            list_item.delete()  # Delete the list

            return JsonResponse({"success": True, "message": "Sėkmingai ištrinta"})
        except ObjectDoesNotExist:
            return JsonResponse({"error": "Irašas nerastas"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    elif request.method == "POST":
        try:
            data = json.loads(request.body)
            list_id = data.get("list_id")
            list_obj = lModels.List.objects.get(id=list_id)

            name = data.get("name")
            qty = data.get("qty")
            assigned_to = data.get("assigned_to")

            match list_obj.list_type:
                case ListType.TASK.name:
                    if assigned_to:
                        assigned_to = FamilyMember.objects.get(pk=assigned_to).user

            try:
                lModels.ListItem.objects.update_or_create(
                    name=name,
                    list_id=list_id,
                    defaults={
                        "qty": qty,
                        "assigned_to": assigned_to
                    }
                )
                return JsonResponse({"success": True})
            except Exception:
                return JsonResponse({"error": "Nepavyko sukurti įrašo"}, status=400)

        except ObjectDoesNotExist:
            return JsonResponse({"error": "List not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Netinkamas kvietimas"}, status=400)

@family_member_required
def list(request):
    if request.method == "DELETE":
        try:
            data = json.loads(request.body)
            list_id = data.get("list_id")

            # Check if the list exists
            family_list = lModels.List.objects.get(pk=list_id)
            family_list.delete()  # Delete the list

            return JsonResponse({"success": True, "message": "Sėkmingai ištrinta"})
        except ObjectDoesNotExist:
            return JsonResponse({"error": "Irašas nerastas"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    elif request.method == "POST":
        try:
            # Parse JSON body
            data = json.loads(request.body)

            name = data.get("name")
            list_type = data.get("list_type")

            # Ensure "datetime" key exists
            if "datetime" not in data:
                return JsonResponse({"error": "Missing 'datetime' field"}, status=400)

            datetimeInt = data.pop("datetime")  # Remove 'datetime' to avoid form issues

            # Convert timestamp to datetime object
            if datetimeInt > 1e10:  # If timestamp is in milliseconds
                datetime_obj = datetime.fromtimestamp(datetimeInt / 1000)
            else:  # If timestamp is in seconds
                datetime_obj = datetime.fromtimestamp(datetimeInt)

            # Make timezone-aware if necessary
            datetime_obj = timezone.make_aware(datetime_obj) if timezone.is_naive(datetime_obj) else datetime_obj

            print(datetime_obj)

            try:
                lModels.List.objects.update_or_create(
                    name=name,
                    list_type=list_type,
                    creator_id=request.user.pk,
                    family_id=request.user.getFamily().pk,
                    defaults={
                        "datetime": datetime_obj
                    }
                )

                return JsonResponse({"success": True})
            except Exception:
                return JsonResponse({"error": "Operacijoj įvyko klaida"}, status=400)

        except ObjectDoesNotExist:
            return JsonResponse({"error": "List not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Netinkamas kvietimas"}, status=400)
