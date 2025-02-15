import json
from django.http import JsonResponse
from django.shortcuts import render
from List.enum import ListType
from Family.models import FamilyMember
from Nestify.decorators import family_member_required
from django.utils import timezone
from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist
from . import models
from Dashboard.views import format_time_difference_in
import tzlocal  # Detects the system's local timezone


# Create your views here.
@family_member_required
def recipes_view(request):
    return render(request, 'recipes/main.html')

@family_member_required
def recipes(request):
    family = request.user.getFamily()
    recipes = models.List.objects.filter(family=family, list_type=ListType.MEAL.name)

    recipe_list = []
    for recipe in recipes:
        recipe_item = models.ListItem.get_list_items(recipe)
        recipe_item_list = []
        for item in recipe_item:
            recipe_item_list.append({
                "id": item.pk,
                "name": item.name,
                "qty": item.qty
            })

        if recipe.image:
            full_image_url = request.build_absolute_uri(recipe.image.url)
        else:
            full_image_url = 'none'

        recipe_list.append({
            "id": recipe.pk,
            "name": recipe.name,
            "image": full_image_url,
            "description": recipe.description,
            "items": recipe_item_list
        })

    return JsonResponse({"recipe_list": recipe_list}, safe=False)

@family_member_required
def update_item_status(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            item_id = data.get("item_id")
            completed = data.get("completed")

            item = models.ListItem.objects.get(pk=item_id)
            item.completed = completed
            item.save()

            return JsonResponse({"success": True, "message": "Sekmingai atnaujinti duomenys"})
        except ObjectDoesNotExist:
            return JsonResponse({"error": "Įrašas nerastas"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Netinkamas kvietimas"}, status=400)

@family_member_required
def get_family_list(request):
    """API endpoint to fetch family list and items."""
    user = request.user
    family = user.getFamily()

    if not family:
        return JsonResponse({"error": "No family found"}, status=400)

    # Fetch lists belonging to the family
    family_lists = models.List.get_family_list(family)
    family_lists = family_lists.order_by("datetime")

    # Convert lists and items to JSON format
    data = []
    for lst in family_lists:
        items = models.ListItem.get_list_items(lst)  # Fetch items for each list

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
            "date": format_time_difference_in(timezone.now(), lst.datetime),
            "items": itemData
        })

    return JsonResponse({"family_list": data}, safe=False)

@family_member_required
def item(request):
    if request.method == "DELETE":
        try:
            data = json.loads(request.body)
            item_id = data.get("item_id")

            # Check if the list exists
            list_item = models.ListItem.objects.get(pk=item_id)
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
            list_obj = models.List.objects.get(id=list_id)

            name = data.get("name")
            qty = data.get("qty")
            assigned_to = data.get("assigned_to")

            match list_obj.list_type:
                case ListType.TASK.name:
                    if assigned_to:
                        assigned_to = FamilyMember.objects.get(pk=assigned_to).user

            try:
                models.ListItem.objects.update_or_create(
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
            family_list = models.List.objects.get(pk=list_id)
            family_list.delete()  # Delete the list

            return JsonResponse({"success": True, "message": "Sėkmingai ištrinta"})
        except ObjectDoesNotExist:
            return JsonResponse({"error": "Irašas nerastas"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    elif request.method == "POST":
        try:
            # Check if the request is multipart/form-data (i.e. contains files)
            if request.content_type.startswith("multipart/form-data"):
                # Use request.POST for non-file fields and request.FILES for file fields.
                data = request.POST.dict()  # Convert QueryDict to a normal dict
                image_file = request.FILES.get("image")
            else:
                # For non-file JSON requests
                data = json.loads(request.body)
                image_file = None

            name = data.get("name")
            list_type = data.get("list_type")
            description = data.get("description")

            # Ensure "datetime" key exists
            if "datetime" not in data:
                return JsonResponse({"error": "Missing 'datetime' field"}, status=400)

            datetimeInt = int(data.pop("datetime"))  # Remove 'datetime' to avoid form issues

            # Convert timestamp to datetime object
            if datetimeInt > 1e10:  # If timestamp is in milliseconds
                datetime_obj = datetime.fromtimestamp(datetimeInt / 1000)
            else:  # If timestamp is in seconds
                datetime_obj = datetime.fromtimestamp(datetimeInt)

            # Make timezone-aware if necessary
            server_tz = tzlocal.get_localzone()

            # Convert naive datetime to server timezone
            datetime_obj = datetime_obj.replace(tzinfo=server_tz)

            # Save or update the list. You might also want to save the image file if provided.
            try:
                obj, created = models.List.objects.update_or_create(
                    name=name,
                    list_type=list_type,
                    creator_id=request.user.pk,
                    family_id=request.user.getFamily().pk,
                    defaults={
                        "datetime": datetime_obj,
                        "description": description
                    }
                )
                # If an image file was provided, handle it here (for example, update the object's image field)
                if image_file:
                    obj.image.save(image_file.name, image_file)
                    obj.save()

                return JsonResponse({"success": True, "list_id": obj.pk})
            except Exception:
                return JsonResponse({"error": "Operacijoj įvyko klaida"}, status=400)

        except ObjectDoesNotExist:
            return JsonResponse({"error": "List not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Netinkamas kvietimas"}, status=400)
