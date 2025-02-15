from django.shortcuts import render
from Nestify.decorators import family_member_required


@family_member_required
def dashboard(request):
    return render(request, 'dashboard/main.html')  # Redirect authenticated users to a dashboard or home page
