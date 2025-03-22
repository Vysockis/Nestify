from django.urls import path
from . import views

urlpatterns = [
    path('', views.finance, name="finance"),
    path('api/dashboard/', views.dashboard, name="finance-dashboard"),
    path('api/categories/', views.categories, name="finance-categories"),
    path('api/scan-receipt/', views.scan_receipt, name="finance-scan-receipt"),
]
