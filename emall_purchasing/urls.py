# emall_purchasing/urls.py
from django.urls import path
from .views import ProcurementSelectView, ProcurementPurchasingListView, ProcurementProgressView
from .views.progress_views import update_purchasing_info
from .views.supplier_views import add_supplier_to_procurement, delete_supplier, update_supplier

urlpatterns = [
    path('procurement/<int:procurement_id>/select/', ProcurementSelectView.as_view(), name='procurement-select'),
    path('procurement/<int:procurement_id>/progress/', ProcurementProgressView.as_view(), name='procurement-progress'),
    path('procurement/purchasing-list/', ProcurementPurchasingListView.as_view(), name='procurement-purchasing-list'),
    path('supplier/<int:supplier_id>/delete/', delete_supplier, name='delete-supplier'),
    path('procurement/<int:procurement_id>/add-supplier/', add_supplier_to_procurement, name='add-supplier'),
    path('procurement/<int:procurement_id>/update/', update_purchasing_info, name='update-purchasing'),
    path('supplier/<int:supplier_id>/update/', update_supplier, name='update_supplier'),
]
