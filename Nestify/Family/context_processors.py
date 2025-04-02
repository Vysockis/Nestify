from .models import FamilyMember

def user_family(request):
    if request.user.is_authenticated:
        family = request.user.getFamily()
        try:
            family_member = FamilyMember.objects.get(user=request.user, accepted=True)
        except FamilyMember.DoesNotExist:
            family_member = None
        return {
            'user_family': family,
            'user_familymember': family_member
        }
    return {
        'user_family': None,
        'user_familymember': None
    }
