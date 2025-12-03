from django.urls import path
from .views import procurement_dashboard_stats, procurement_status_stats, procurement_status_stats_by_owner

app_name = 'analysis'

urlpatterns = [
    path('dashboard-stats/', procurement_dashboard_stats, name='dashboard_stats'),
    path('status-stats/', procurement_status_stats, name='status_stats'),
    path('status-stats-owner/', procurement_status_stats_by_owner, name='status_stats_owner'),
]
