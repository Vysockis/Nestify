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
                    name = f"{f"{item.qty}x" if item.qty is not None and item.qty != 1 else ""} {item.name}"
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
            qty = data.get("quantity")
            price = data.get("price")  # We'll use this value for the amount field
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
                        "amount": price,  # Store price in the amount field
                        "assigned_to": assigned_to
                    }
                )
                return JsonResponse({"success": True})
            except Exception as e:
                return JsonResponse({"error": f"Nepavyko sukurti įrašo: {str(e)}"}, status=400)

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
            amount = data.get("amount")
            category_id = data.get("category")

            # Ensure "datetime" key exists
            if "datetime" not in data:
                return JsonResponse({"error": "Missing 'datetime' field"}, status=400)

            # Handle datetime conversion
            try:
                datetime_str = data["datetime"]
                try:
                    # First try to parse as timestamp (milliseconds)
                    datetime_obj = datetime.fromtimestamp(int(datetime_str) / 1000, tz=timezone.get_current_timezone())
                except (ValueError, TypeError):
                    # If not a timestamp, try parsing as ISO format string
                    datetime_obj = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                    # Make timezone-aware if necessary
                    if datetime_obj.tzinfo is None:
                        datetime_obj = timezone.make_aware(datetime_obj)
            except Exception as e:
                return JsonResponse({"error": f"Invalid datetime format: {str(e)}"}, status=400)

            # Save or update the list. You might also want to save the image file if provided.
            try:
                defaults = {
                    "datetime": datetime_obj,
                    "description": description
                }

                # Add finance-specific fields if it's a finance operation
                if list_type == ListType.FINANCE.name:
                    defaults["amount"] = amount
                    defaults["category_id"] = category_id

                obj, created = models.List.objects.update_or_create(
                    name=name,
                    list_type=list_type,
                    creator_id=request.user.pk,
                    family_id=request.user.getFamily().pk,
                    defaults=defaults
                )

                # If an image file was provided, handle it here
                if image_file:
                    obj.image.save(image_file.name, image_file)
                    obj.save()

                return JsonResponse({"success": True, "list_id": obj.pk})
            except Exception as e:
                return JsonResponse({"error": f"Operacijoj įvyko klaida: {str(e)}"}, status=400)

        except ObjectDoesNotExist:
            return JsonResponse({"error": "List not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Netinkamas kvietimas"}, status=400)

@family_member_required
def items(request):
    if request.method == "GET":
        try:
            list_id = request.GET.get("list_id")
            if not list_id:
                return JsonResponse({"error": "Missing list_id parameter"}, status=400)

            # Check if the list exists and belongs to the user's family
            user = request.user
            family = user.getFamily()

            try:
                list_obj = models.List.objects.get(pk=list_id, family=family)
            except ObjectDoesNotExist:
                return JsonResponse({"error": "List not found"}, status=404)

            # Fetch items for the list
            items = models.ListItem.get_list_items(list_obj)

            # Convert items to JSON format
            items_data = []
            for item in items:
                item_data = {
                    "id": item.pk,
                    "name": item.name,
                    "quantity": item.qty,
                    "price": item.amount,  # Use amount field as price
                    "completed": item.completed
                }

                # Add assigned_to if it exists
                if item.assigned_to:
                    item_data["assigned_to"] = {
                        "id": item.assigned_to.pk,
                        "name": f"{item.assigned_to.first_name} {item.assigned_to.last_name}"
                    }

                items_data.append(item_data)

            return JsonResponse({"success": True, "items": items_data}, safe=False)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Netinkamas kvietimas"}, status=400)
