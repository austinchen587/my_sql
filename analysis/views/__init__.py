# analysis/views/__init__.py
from .dashboard_views import procurement_dashboard_stats
from .status_stats_views import procurement_status_stats
from .status_stats_owner_views import procurement_status_stats_by_owner
from .daily_profit_views import daily_profit_stats
from .final_quote_views import update_final_quote  # 新增导入
from .ht_emall_views import ht_emall_records
from .ht_emall_reverse_views import ht_emall_reverse_records
from .project_profit_views import project_profit_stats
from .monthly_profit_views import monthly_profit_summary

__all__ = [
    'procurement_dashboard_stats',
    'procurement_status_stats',
    'procurement_status_stats_by_owner',
    'daily_profit_stats',
    'update_final_quote',  # 新增
    'ht_emall_records',
    'ht_emall_reverse_records',
    'project_profit_stats',
    'monthly_profit_summary'
]
