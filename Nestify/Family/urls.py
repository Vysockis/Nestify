from django.urls import path
from . import views

urlpatterns = [
    path('api/members/', views.members, name="members"),
]
