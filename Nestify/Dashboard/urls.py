from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name="dashboard"),
    path('calendar/', views.calendar, name="calendar"),
    path('calendar/api/events/', views.calendar_events, name="calendar-events"),
    path('notifications/<int:notification_id>/mark-read/', views.mark_notification_read, name="mark-notification-read"),
    path('smart/', views.smart_dashboard, name='smart-dashboard'),
    path('smart/device/<int:device_id>/toggle/', views.toggle_device, name='toggle-device'),
    path('smart/device/<int:device_id>/brightness/', views.update_brightness, name='update-brightness'),
    path('smart/device/<int:device_id>/delete/', views.delete_device, name='delete-device'),
    path('smart/device/add/', views.add_device, name='add-device'),
]
