from django.urls import path
from . import views

urlpatterns = [
    path('', views.plan_view, name="plans-view"),
    path('api/plans/', views.plans, name="plans"),
    path('api/plan/', views.plan, name="plan"),
]
