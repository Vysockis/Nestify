import json
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
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

        # If task is completed and has points, create PrizeTask
        if item.completed and item.amount and item.amount > 0 and item.assigned_to:
            family_member = FamilyMember.objects.get(user=item.assigned_to)
            # Check if PrizeTask doesn't already exist
            prize_task, created = models.PrizeTask.objects.get_or_create(
                list_item=item,
                family_member=family_member,
                defaults={
                    "points": item.amount
                }
            )

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
            points_text = f" - {int(item.amount)}💎" if item.amount and item.amount > 0 else ""
            user_text = f"{item.assigned_to.first_name}: " if item.assigned_to else ""
            text = f"{user_text}{item.name}{points_text}"
            return text
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
                    "amount": data.get("price") if data.get("price") is not None else data.get("amount"),
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

    if request.method == "POST":
        try:
            data = request.POST
            image_file = request.FILES.get("image")

            # Check if a recipe with the same name already exists
            existing_recipe = models.List.objects.filter(
                family=request.user.getFamily(),
                list_type=ListType.MEAL.name,
                name=data.get("name")
            ).first()

            if existing_recipe:
                return JsonResponse({
                    "error": "Toks receptas jau egzistuoja",
                    "success": False
                }, status=400)

            defaults = {
                "description": data.get("description"),
                "datetime": data.get("datetime")
            }

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

@family_member_required
def prizes_view(request):
    return render(request, 'prizes/main.html')

@family_member_required
def get_points_data(request):
    family = request.user.getFamily()
    family_member = FamilyMember.objects.get(user=request.user, family=family)
    
    # Get user's points
    user_points = models.PointsTransaction.get_member_points(family_member)
    
    # Get leaderboard
    leaderboard = models.PointsTransaction.get_family_leaderboard(family)
    leaderboard_data = [{
        "id": member.id,
        "name": member.user.first_name,
        "points": member.total_points or 0,
        "is_current_user": member.user == request.user
    } for member in leaderboard]
    
    # Get available prizes
    prizes = models.Prize.get_family_prizes(family)
    prizes_data = [{
        "id": prize.id,
        "name": prize.name,
        "points_required": prize.points_required,
        "is_available": user_points >= prize.points_required
    } for prize in prizes]
    
    # Get redeemed prizes
    if family_member.admin:
        # For admin, get all family members' redeemed prizes
        redeemed_prizes = models.PointsTransaction.objects.filter(
            family_member__family=family,
            transaction_type=models.PointsTransaction.PRIZE_REDEMPTION
        ).order_by('-created_at')
    else:
        # For regular users, get only their redeemed prizes
        redeemed_prizes = models.PointsTransaction.objects.filter(
            family_member=family_member,
            transaction_type=models.PointsTransaction.PRIZE_REDEMPTION
        ).order_by('-created_at')
    
    redeemed_prizes_data = [{
        "name": models.Prize.objects.get(id=int(t.reference_id.split('_')[1])).name,
        "points": abs(t.points),
        "date": t.created_at.strftime("%Y-%m-%d %H:%M"),
        "member_name": t.family_member.user.first_name if family_member.admin else None
    } for t in redeemed_prizes]
    
    return JsonResponse({
        "points": user_points,
        "leaderboard": leaderboard_data,
        "prizes": prizes_data,
        "redeemed_prizes": redeemed_prizes_data,
        "is_admin": family_member.admin
    })

@family_member_required
@parent_required
def get_pending_tasks(request):
    family = request.user.getFamily()
    pending_tasks = models.PrizeTask.get_pending_tasks(family)
    
    tasks_data = [{
        "id": task.id,
        "task_name": task.list_item.name,
        "member_name": task.family_member.user.first_name,
        "points": task.points,
        "created_at": task.created_at.isoformat()
    } for task in pending_tasks]
    
    return JsonResponse({"pending_tasks": tasks_data})

@family_member_required
@parent_required
def approve_task(request, task_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)
        
    try:
        task = models.PrizeTask.objects.get(pk=task_id)
        
        # Create points transaction
        models.PointsTransaction.objects.create(
            family_member=task.family_member,
            points=task.points,
            transaction_type=models.PointsTransaction.TASK_COMPLETION,
            reference_id=f"task_{task.list_item.id}",
            created_by=request.user,
            note=f"Task completion: {task.list_item.name}"
        )
        
        # Update task status
        task.is_approved = True
        task.approved_by = request.user
        task.approved_at = timezone.now()
        task.save()
        
        return JsonResponse({"success": True})
    except models.PrizeTask.DoesNotExist:
        return JsonResponse({"error": "Task not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@family_member_required
@parent_required
def manage_prize(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            family = request.user.getFamily()
            
            models.Prize.objects.create(
                family=family,
                name=data["name"],
                points_required=data["points_required"]
            )
            
            return JsonResponse({"success": True})
        except KeyError:
            return JsonResponse({"error": "Missing required fields"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
            
    elif request.method == "DELETE":
        try:
            data = json.loads(request.body)
            prize = models.Prize.objects.get(pk=data["prize_id"])
            prize.is_active = False
            prize.save()
            return JsonResponse({"success": True})
        except models.Prize.DoesNotExist:
            return JsonResponse({"error": "Prize not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    
    return JsonResponse({"error": "Invalid request method"}, status=400)

@family_member_required
@parent_required
def add_points(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)
        
    try:
        data = json.loads(request.body)
        family = request.user.getFamily()
        member = FamilyMember.objects.get(pk=data["member_id"], family=family)
        
        models.PointsTransaction.objects.create(
            family_member=member,
            points=data["points"],
            transaction_type=models.PointsTransaction.MANUAL_ADDITION,
            created_by=request.user,
            note=data.get("note", "Manual points addition")
        )
        
        return JsonResponse({"success": True})
    except FamilyMember.DoesNotExist:
        return JsonResponse({"error": "Member not found"}, status=404)
    except KeyError:
        return JsonResponse({"error": "Missing required fields"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@family_member_required
@parent_required
def delete_pending_task(request, task_id):
    if request.method != "DELETE":
        return JsonResponse({"error": "Invalid request method"}, status=400)
        
    try:
        task = models.PrizeTask.objects.get(pk=task_id)
        task.delete()
        return JsonResponse({"success": True})
    except models.PrizeTask.DoesNotExist:
        return JsonResponse({"error": "Task not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@family_member_required
def redeem_prize(request, prize_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)
        
    try:
        family = request.user.getFamily()
        family_member = FamilyMember.objects.get(user=request.user, family=family)
        prize = models.Prize.objects.get(pk=prize_id, family=family, is_active=True)
        
        # Check if user has enough points
        current_points = models.PointsTransaction.get_member_points(family_member)
        if current_points < prize.points_required:
            return JsonResponse({"error": "Nepakanka taškų prizui iškeisti"}, status=400)
            
        # Create negative points transaction for prize redemption
        models.PointsTransaction.objects.create(
            family_member=family_member,
            points=-prize.points_required,  # Negative points for redemption
            transaction_type=models.PointsTransaction.PRIZE_REDEMPTION,
            reference_id=f"prize_{prize.id}",
            created_by=request.user,
            note=f"Prizas iškeistas: {prize.name}"
        )
        
        return JsonResponse({"success": True})
    except models.Prize.DoesNotExist:
        return JsonResponse({"error": "Prizas nerastas"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
