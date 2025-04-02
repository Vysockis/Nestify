from Family.models import FamilyMember

def user_role(request):
    if request.user.is_authenticated:
        try:
            family = request.user.getFamily()
            if family:
                family_member = FamilyMember.objects.get(family=family, user=request.user)
                return {
                    'is_kid': family_member.kid
                }
        except (FamilyMember.DoesNotExist, AttributeError):
            pass
    return {'is_kid': False} 