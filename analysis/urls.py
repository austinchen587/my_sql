from django.urls import path
from .views import procurement_dashboard_stats, procurement_status_stats

app_name = 'analysis'

urlpatterns = [
    path('dashboard-stats/', procurement_dashboard_stats, name='dashboard_stats'),
    path('status-stats/', procurement_status_stats, name='status_stats'),
]
