from django.urls import path
from . import views

urlpatterns = [
    path('', views.finance, name="finance"),
    path('api/dashboard/', views.dashboard, name="finance-dashboard"),
    path('api/categories/', views.categories, name="categories"),
]
