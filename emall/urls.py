from django.urls import path
from .views import ProcurementListView, ProcurementListDataView, ProcurementDetailView

urlpatterns = [
    path('', ProcurementListView.as_view(), name='procurement-home'),
    path('procurements/', ProcurementListDataView.as_view(), name='procurement-list'),
    path('procurements/<int:pk>/', ProcurementDetailView.as_view(), name='procurement-detail'),
]
