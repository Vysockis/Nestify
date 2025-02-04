from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name="dashboard"),
    path('api/family-list/', views.get_family_list, name="get_family_list"),
    path('api/update-item-status/', views.update_item_status, name="update_item_status"),
    path('api/item/', views.item, name="item"),
    path('api/list/', views.list, name="list"),
]
