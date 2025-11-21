from django.urls import path
from . import views

app_name = 'emall_purchasing'

urlpatterns = [
    path('procurements/<int:procurement_id>/select/', views.ProcurementSelectView.as_view(), name='procurement_select'),
    path('procurements/<int:procurement_id>/progress/', views.ProcurementProgressView.as_view(), name='procurement_progress'),
    path('purchasing-list/', views.ProcurementPurchasingListView.as_view(), name='purchasing_list'),
]
