from django.http import JsonResponse
from Nestify.decorators import family_member_required

# Create your views here.
@family_member_required
def members(request):
    """API endpoint to fetch family list and items."""
    user = request.user
    family_members = user.getFamily().get_family_members()

    members = []
    for member in family_members:
        members.append({
            "id": member.pk,
            "name": member.user.first_name,
            "surname": member.user.last_name,
            "kid": member.kid,
            "admin": member.admin,
            "current": True if member.user == user else False
        })

    return JsonResponse({"family_members": members}, safe=False)
