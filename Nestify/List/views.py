import json
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist
from List.enum import ListType
from Family.models import FamilyMember
from Nestify.decorators import family_member_required, parent_required
from Dashboard.views import format_time_difference_in
from . import models


# Create your views here.
@family_member_required
def recipes_view(request):
    return render(request, 'recipes/main.html')

@family_member_required
def recipes(request):
    family = request.user.getFamily()
    recipes = models.List.objects.filter(family=family, list_type=ListType.MEAL.name)
    
    recipe_list = [{
        "id": recipe.pk,
        "name": recipe.name,
        "image": request.build_absolute_uri(recipe.image.url) if recipe.image else None,
        "description": recipe.description,
        "items": [{
            "id": item.pk,
            "name": item.name,
            "qty": item.qty
        } for item in models.ListItem.get_list_items(recipe)]
    } for recipe in recipes]

    return JsonResponse({"recipe_list": recipe_list}, safe=False)

@family_member_required
def update_item_status(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)
        
    try:
        data = json.loads(request.body)
        item = models.ListItem.objects.get(pk=data.get("item_id"))
        item.completed = data.get("completed")
        item.save()
        return JsonResponse({"success": True, "message": "Item status updated successfully"})
    except ObjectDoesNotExist:
        return JsonResponse({"error": "Item not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@family_member_required
def get_family_list(request):
    family = request.user.getFamily()
    if not family:
        return JsonResponse({"error": "No family found"}, status=400)

    family_lists = models.List.get_family_list(family).order_by("datetime")
    
    def format_item_name(item, list_type):
        if list_type == ListType.GROCERY.name:
            return f"{f"{item.qty}x" if item.qty and item.qty != 1 else ""} {item.name}"
        elif list_type == ListType.TASK.name:
            user_text = f"{item.assigned_to.first_name}: " if item.assigned_to else ""
            return f"{user_text}{item.name}"
        elif list_type == ListType.MEAL.name:
            return f"{item.qty or 0}x {item.name}"
        return item.name

    data = [{
        "id": lst.id,
        "type": lst.list_type,
        "name": lst.name,
        "date": format_time_difference_in(timezone.now(), lst.datetime),
        "items": [{
            "id": item.pk,
            "name": format_item_name(item, lst.list_type),
            "completed": item.completed
        } for item in models.ListItem.get_list_items(lst)]
    } for lst in family_lists]

    return JsonResponse({"family_list": data}, safe=False)

@family_member_required
@parent_required
def item(request):
    if request.method == "DELETE":
        try:
            data = json.loads(request.body)
            models.ListItem.objects.get(pk=data.get("item_id")).delete()
            return JsonResponse({"success": True, "message": "Item deleted successfully"})
        except ObjectDoesNotExist:
            return JsonResponse({"error": "Item not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    elif request.method == "POST":
        try:
            data = json.loads(request.body)
            list_obj = models.List.objects.get(id=data.get("list_id"))
            
            assigned_to = None
            if list_obj.list_type == ListType.TASK.name and data.get("assigned_to"):
                assigned_to = FamilyMember.objects.get(pk=data.get("assigned_to")).user
                # Create notification for task assignment
                from Family.models import Notification, FamilySettings
                
                # Get family settings and notification recipients
                settings = FamilySettings.get_or_create_settings(list_obj.family)
                recipients = settings.get_notification_recipients('task', assigned_user=assigned_to)
                
                # Create notification for each recipient
                for recipient in recipients:
                    # Different message based on whether recipient is the assigned user
                    if recipient == assigned_to:
                        message = f'Jums priskirta nauja užduotis: {data.get("name")} ({list_obj.name})'
                    else:
                        message = f'{assigned_to.first_name} priskirta nauja užduotis: {data.get("name")} ({list_obj.name})'
                    
                    Notification.create_notification(
                        family=list_obj.family,
                        recipient=recipient,
                        notification_type='task_assigned',
                        title='Naujas užduoties priskyrimas',
                        message=message,
                        sender=request.user,
                        related_object_id=list_obj.id
                    )

            models.ListItem.objects.update_or_create(
                name=data.get("name"),
                list_id=data.get("list_id"),
                defaults={
                    "qty": data.get("qty"),
                    "amount": data.get("price"),
                    "assigned_to": assigned_to
                }
            )
            return JsonResponse({"success": True})
        except ObjectDoesNotExist:
            return JsonResponse({"error": "List not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=400)

@family_member_required
@parent_required
def list(request):
    if request.method == "DELETE":
        try:
            data = json.loads(request.body)
            models.List.objects.get(pk=data.get("list_id")).delete()
            return JsonResponse({"success": True, "message": "List deleted successfully"})
        except ObjectDoesNotExist:
            return JsonResponse({"error": "List not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    elif request.method == "POST":
        try:
            if request.content_type.startswith("multipart/form-data"):
                data = request.POST.dict()
                image_file = request.FILES.get("image")
            else:
                data = json.loads(request.body)
                image_file = None

            if "datetime" not in data:
                return JsonResponse({"error": "Missing datetime field"}, status=400)

            try:
                datetime_str = data["datetime"]
                try:
                    datetime_obj = datetime.fromtimestamp(int(datetime_str) / 1000, tz=timezone.get_current_timezone())
                except (ValueError, TypeError):
                    datetime_obj = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                    if datetime_obj.tzinfo is None:
                        datetime_obj = timezone.make_aware(datetime_obj)
            except Exception as e:
                return JsonResponse({"error": f"Invalid datetime format: {str(e)}"}, status=400)

            defaults = {
                "datetime": datetime_obj,
                "description": data.get("description")
            }

            if data.get("list_type") == ListType.FINANCE.name:
                defaults.update({
                    "amount": data.get("amount"),
                    "category_id": data.get("category")
                })

            obj, _ = models.List.objects.update_or_create(
                name=data.get("name"),
                list_type=data.get("list_type"),
                creator_id=request.user.pk,
                family_id=request.user.getFamily().pk,
                defaults=defaults
            )

            if image_file:
                obj.image.save(image_file.name, image_file)
                obj.save()

            return JsonResponse({"success": True, "list_id": obj.id})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=400)

@family_member_required
def items(request):
    if request.method != "GET":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    try:
        list_id = request.GET.get("list_id")
        if not list_id:
            return JsonResponse({"error": "List ID is required"}, status=400)

        list_obj = models.List.objects.get(pk=list_id)
        items = models.ListItem.get_list_items(list_obj)

        return JsonResponse({
            "items": [{
                "id": item.pk,
                "name": item.name,
                "qty": item.qty,
                "completed": item.completed,
                "price": item.amount,
                "assigned_to": item.assigned_to.user.pk if item.assigned_to else None
            } for item in items]
        })
    except ObjectDoesNotExist:
        return JsonResponse({"error": "List not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
