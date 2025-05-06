from django.urls import path
from . import views

urlpatterns = [
    path(
        '',
        views.finance,
        name="finance"),
    path(
        'api/dashboard/',
        views.dashboard,
        name="finance-dashboard"),
    path(
        'api/categories/',
        views.categories,
        name="finance-categories"),
    path(
        'api/scan-receipt/',
        views.scan_receipt,
        name="finance-scan-receipt"),
    path(
        'api/operations/<int:operation_id>/delete/',
        views.delete_operation,
        name="finance-delete-operation"),
    path(
        'api/operations/<int:operation_id>/edit/',
        views.edit_operation,
        name="finance-edit-operation"),
    path(
        'api/operation-items/<int:item_id>/edit/',
        views.edit_operation_item,
        name="finance-edit-operation-item"),
]
