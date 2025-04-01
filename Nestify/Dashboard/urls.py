from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name="dashboard"),
    path('calendar/', views.calendar, name="calendar"),
    path('calendar/api/events/', views.calendar_events, name="calendar-events"),
    path('notifications/<int:notification_id>/mark-read/', views.mark_notification_read, name="mark-notification-read"),
]
