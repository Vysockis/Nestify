from django.urls import path
from . import views
from . import webhooks

urlpatterns = [
    path('members/', views.members, name='family_members'),
    path('settings/', views.family_settings, name='family_settings'),
    path('manage/', views.manage, name='family_manage'),
    path('settings/api/', views.settings_api, name='family_settings_api'),
    path('webhook/', webhooks.stripe_webhook, name='stripe_webhook'),
    path('payment/required/', views.payment_required, name='payment_required'),
    path('payment/create/<int:family_id>/', views.create_stripe_session, name='create_stripe_session'),
]
