from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name="landing"),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    
    # Family management
    path('family/manage/', views.manage_family, name='manage_family'),
    path('family/api/generate-code/', views.generate_invitation_code, name='generate_invitation_code'),
    path('family/api/delete-code/<int:code_id>/', views.delete_invitation_code, name='delete_invitation_code'),
    path('family/api/toggle-kid/<int:member_id>/', views.toggle_kid_status, name='toggle_kid_status'),
    path('family/api/remove-member/<int:member_id>/', views.remove_family_member, name='remove_family_member'),
]
