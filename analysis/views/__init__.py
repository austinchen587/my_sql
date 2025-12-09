# analysis/views/__init__.py
from .dashboard_views import procurement_dashboard_stats
from .status_stats_views import procurement_status_stats
from .status_stats_owner_views import procurement_status_stats_by_owner
from .daily_profit_views import daily_profit_stats
from .final_quote_views import update_final_quote  # 新增导入

__all__ = [
    'procurement_dashboard_stats',
    'procurement_status_stats',
    'procurement_status_stats_by_owner',
    'daily_profit_stats',
    'update_final_quote'  # 新增
]
