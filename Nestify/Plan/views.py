import json
from django.http import JsonResponse
from django.shortcuts import render
import tzlocal
from Family.models import FamilyMember
from Nestify.decorators import family_member_required
from django.utils import timezone
from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist
from . import models
from Dashboard.views import format_time_difference_in

# Create your views here.
@family_member_required
def plan(request):
    if request.method == "DELETE":
        try:
            data = json.loads(request.body)
            models.Plan.objects.get(pk=data.get("plan_id")).delete()
            return JsonResponse({"success": True, "message": "Plan deleted successfully"})
        except ObjectDoesNotExist:
            return JsonResponse({"error": "Plan not found"}, status=404)
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

            datetime_str = data.pop("datetime")
            try:
                datetime_obj = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            except ValueError:
                try:
                    datetime_int = int(datetime_str)
                    datetime_obj = datetime.fromtimestamp(
                        datetime_int / 1000 if datetime_int > 1e10 else datetime_int
                    )
                except ValueError:
                    return JsonResponse({"error": "Invalid datetime format"}, status=400)

            datetime_obj = datetime_obj.replace(tzinfo=tzlocal.get_localzone())

            plan_id = data.get("plan_id")
            if plan_id:
                obj = models.Plan.objects.get(pk=plan_id)
                obj.name = data.get("name")
                obj.plan_type = data.get("plan_type")
                obj.description = data.get("description")
                obj.datetime = datetime_obj
                if image_file:
                    obj.image.save(image_file.name, image_file)
                obj.save()
            else:
                obj = models.Plan.objects.create(
                    name=data.get("name"),
                    plan_type=data.get("plan_type"),
                    creator_id=request.user.pk,
                    family_id=request.user.getFamily().pk,
                    datetime=datetime_obj,
                    description=data.get("description")
                )
                if image_file:
                    obj.image.save(image_file.name, image_file)
                    obj.save()

            return JsonResponse({"success": True, "plan_id": obj.pk})
        except ObjectDoesNotExist:
            return JsonResponse({"error": "Plan not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=400)

@family_member_required
def member(request):
    if request.method == "DELETE":
        try:
            data = json.loads(request.body)
            member = FamilyMember.objects.get(pk=data.get("member_id"))
            plan = models.Plan.objects.get(pk=data.get("plan_id"))
            models.PlanMember.objects.get(user=member, plan=plan).delete()
            return JsonResponse({"success": True, "message": "Member removed successfully"})
        except ObjectDoesNotExist:
            return JsonResponse({"error": "Member or plan not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    elif request.method == "POST":
        try:
            data = json.loads(request.body)
            member = FamilyMember.objects.get(pk=data.get("member_id"))
            plan = models.Plan.objects.get(pk=data.get("plan_id"))
            
            obj, _ = models.PlanMember.objects.update_or_create(
                plan=plan,
                user=member
            )
            return JsonResponse({"success": True, "plan_member_id": obj.pk})
        except ObjectDoesNotExist:
            return JsonResponse({"error": "Member or plan not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=400)

@family_member_required
def plan_view(request):
    plan_id = request.GET.get("planId") or request.POST.get("planId")
    return render(request, 'plans/main.html', {"plan_id": plan_id})

@family_member_required
def plans(request):
    family = request.user.getFamily()
    plans = models.Plan.objects.filter(family=family)

    plan_list = [{
        "id": plan.pk,
        "name": plan.name,
        "description": plan.description,
        "image": request.build_absolute_uri(plan.image.url) if plan.image else None,
        "date_formatted": format_time_difference_in(timezone.now(), plan.datetime),
        "datetime": plan.datetime,
        "members": [{
            "id": member.user.pk,
            "name": member.user.user.first_name
        } for member in models.PlanMember.get_plan_members(plan)],
        "listId": plan.get_list().pk if plan.get_list() else 0,
        "listitems": [{
            "id": item.pk,
            "name": item.name,
            "qty": item.qty
        } for item in plan.get_list_item()]
    } for plan in plans]

    return JsonResponse({"plan_list": plan_list}, safe=False)
