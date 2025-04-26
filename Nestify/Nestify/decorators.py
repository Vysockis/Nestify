from django.shortcuts import redirect
from django.core.exceptions import ObjectDoesNotExist
from functools import wraps
from Family.models import FamilyMember  # Import your model
from django.contrib import messages

def family_member_required(view_func):
    """ Custom decorator to check if the user is in FamilyMember model. """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:  # Check if user is logged in
            return redirect('/login/')  # Redirect unauthenticated users to login

        try:
            # Check if user exists in FamilyMember model
            FamilyMember.objects.get(user=request.user, accepted=True)
        except ObjectDoesNotExist:
            messages.error(request, 'Jūs nesate šeimos narys.')
            return redirect('/')  # Redirect if user is NOT a family member

        return view_func(request, *args, **kwargs)

    return _wrapped_view

def parent_required(view_func):
    """ Custom decorator to check if the user is not a kid. """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/login/')

        try:
            member = FamilyMember.objects.get(user=request.user, accepted=True)
            if member.kid:
                messages.error(request, 'Ši funkcija prieinama tik tėvams.')
                return redirect('/dashboard/')  # Redirect kids to dashboard
        except ObjectDoesNotExist:
            messages.error(request, 'Jūs nesate šeimos narys.')
            return redirect('/')

        return view_func(request, *args, **kwargs)

    return _wrapped_view
