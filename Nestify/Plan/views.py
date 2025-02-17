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
            plan_id = data.get("plan_id")

            # Check if the list exists
            family_plan = models.Plan.objects.get(pk=plan_id)
            family_plan.delete()  # Delete the list

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
            plan_type = data.get("plan_type")
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
                obj, created = models.Plan.objects.update_or_create(
                    name=name,
                    plan_type=plan_type,
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

                return JsonResponse({"success": True, "plan_id": obj.pk})
            except Exception as e:
                print(e)
                return JsonResponse({"error": "Operacijoj įvyko klaida"}, status=400)

        except ObjectDoesNotExist:
            return JsonResponse({"error": "List not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Netinkamas kvietimas"}, status=400)

@family_member_required
def member(request):
    if request.method == "DELETE":
        try:
            data = json.loads(request.body)
            member_id = data.get("member_id")
            plan_id = data.get("plan_id")
            member = FamilyMember.objects.get(pk=member_id)
            family_plan = models.Plan.objects.get(pk=plan_id)

            # Check if the list exists
            plan_member = models.PlanMember.objects.get(user=member, plan=family_plan)
            plan_member.delete()  # Delete the list

            return JsonResponse({"success": True, "message": "Sėkmingai ištrinta"})
        except ObjectDoesNotExist:
            return JsonResponse({"error": "Irašas nerastas"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    elif request.method == "POST":
        try:
            data = json.loads(request.body)
            member_id = data.get("member_id")
            plan_id = data.get("plan_id")
            member = FamilyMember.objects.get(pk=member_id)
            family_plan = models.Plan.objects.get(pk=plan_id)
            # Save or update the list. You might also want to save the image file if provided.
            try:
                obj, created = models.PlanMember.objects.update_or_create(
                    plan=family_plan,
                    user=member
                )

                return JsonResponse({"success": True, "plan_member_id": obj.pk})
            except Exception as e:
                print(e)
                return JsonResponse({"error": "Operacijoj įvyko klaida"}, status=400)

        except ObjectDoesNotExist:
            return JsonResponse({"error": "List not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Netinkamas kvietimas"}, status=400)

@family_member_required
def plan_view(request):
    # Get planId from GET or POST request
    plan_id = request.GET.get("planId") or request.POST.get("planId")

    return render(request, 'plans/main.html', {"plan_id": plan_id})

@family_member_required
def plans(request):
    family = request.user.getFamily()
    plans = models.Plan.objects.filter(family=family)

    plan_list = []
    for plan in plans:
        list_item = plan.get_list_item()
        plan_list_item = []
        for item in list_item:
            plan_list_item.append({
                "id": item.pk,
                "name": item.name,
                "qty": item.qty
            })


        members = models.PlanMember.get_plan_members(plan)
        member_list = []
        for member in members:
            member_list.append({
                "id": member.pk,
                "name": member.user.user.first_name
            })

        if plan.image:
            full_image_url = request.build_absolute_uri(plan.image.url)
        else:
            full_image_url = 'none'

        plan_list.append({
            "id": plan.pk,
            "name": plan.name,
            "description": plan.description,
            "image": full_image_url,
            "date": format_time_difference_in(timezone.now(), plan.datetime),
            "members": member_list,
            "listId": plan.get_list().pk if plan.get_list() else 0,
            "listitems": plan_list_item
        })

    return JsonResponse({"plan_list": plan_list}, safe=False)
