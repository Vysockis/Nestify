from django.urls import path
from . import views

urlpatterns = [
    path('api/members/', views.members, name="members"),
    path('api/settings/', views.settings_api, name="family-settings-api"),
    path('manage/', views.manage, name="family-manage"),
]
