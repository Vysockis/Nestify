from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.inventory_dashboard, name='dashboard'),
    path('items/', views.item_list, name='items'),
    path('items/add/', views.add_item, name='add_item'),
    path('items/<int:item_id>/edit/', views.edit_item, name='edit_item'),
    path('items/<int:item_id>/delete/', views.delete_item, name='delete_item'),
    path('api/items/', views.api_items, name='api_items'),
    path('api/operations/<int:operation_id>/delete/', views.delete_operation, name='delete_operation'),
]
