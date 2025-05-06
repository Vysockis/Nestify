from django.urls import path
from . import views
from . import webhooks

urlpatterns = [
    # Family management
    path('create/', views.create_family, name='create_family'),
    path('manage/', views.manage, name='family_manage'),
    path('join/', views.join_family, name='join_family'),
    path(
        'join/cancel/',
        views.cancel_join_request,
        name='cancel_join_request'),

    # API endpoints
    path(
        'api/generate-code/',
        views.generate_invitation_code,
        name='generate_invitation_code'),
    path(
        'api/delete-code/<int:code_id>/',
        views.delete_invitation_code,
        name='delete_invitation_code'),
    path(
        'api/approve-member/<int:member_id>/',
        views.approve_member,
        name='approve_member'),
    path(
        'api/reject-member/<int:member_id>/',
        views.reject_member,
        name='reject_member'),
    path(
        'api/toggle-kid/<int:member_id>/',
        views.toggle_kid_status,
        name='toggle_kid_status'),
    path(
        'api/remove-member/<int:member_id>/',
        views.remove_family_member,
        name='remove_family_member'),

    # Existing endpoints
    path('members/', views.members, name='family_members'),
    path('settings/', views.family_settings, name='family_settings'),
    path('settings/api/', views.settings_api, name='family_settings_api'),
    path('webhook/', webhooks.stripe_webhook, name='stripe_webhook'),
    path('payment/required/', views.payment_required, name='payment_required'),
    path(
        'payment/create/<int:family_id>/',
        views.create_stripe_session,
        name='create_stripe_session'),
]
