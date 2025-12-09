# analysis/urls.py
from django.urls import path
from .views import (
    procurement_dashboard_stats, 
    procurement_status_stats, 
    procurement_status_stats_by_owner,
    daily_profit_stats,
    update_final_quote  # 新增导入
)

app_name = 'analysis'

urlpatterns = [
    path('dashboard-stats/', procurement_dashboard_stats, name='dashboard_stats'),
    path('status-stats/', procurement_status_stats, name='status_stats'),
    path('status-stats-owner/', procurement_status_stats_by_owner, name='status_stats_owner'),
    path('daily-profit-stats/', daily_profit_stats, name='daily_profit_stats'),
    path('update-final-quote/', update_final_quote, name='update_final_quote'),  # 新增路由
]
