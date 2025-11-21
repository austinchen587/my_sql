# emall_purchasing/urls.py
from django.urls import path
from .views import ProcurementSelectView, ProcurementPurchasingListView, ProcurementProgressView

urlpatterns = [
    path('procurement/<int:procurement_id>/select/', ProcurementSelectView.as_view(), name='procurement-select'),
    path('procurement/<int:procurement_id>/progress/', ProcurementProgressView.as_view(), name='procurement-progress'),
    path('procurement/purchasing-list/', ProcurementPurchasingListView.as_view(), name='procurement-purchasing-list'),
]
