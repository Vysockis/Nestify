from django.shortcuts import render
from Nestify.decorators import family_member_required

# Create your views here.
@family_member_required
def recipes(request):
    print("e")
    return render(request, 'recipes/main.html')
