from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.inventory_dashboard, name='dashboard'),
    path('items/', views.item_list, name='items'),
    path('add/', views.add_item, name='add_item'),
    path('edit/<int:item_id>/', views.edit_item, name='edit_item'),
    path('delete/<int:item_id>/', views.delete_item, name='delete_item'),
    path('api/items/', views.api_items, name='api_items'),
    path('api/operations/<int:operation_id>/delete/', views.delete_operation, name='delete_operation'),
    path('api/operations/<int:operation_id>/update/', views.update_operation, name='update_operation'),
    path('api/expiring-items/', views.api_expiring_items, name='api_expiring_items'),
    path('api/contracts/<int:item_id>/delete/', views.delete_contract, name='delete_contract'),
]
