# views/__init__.py

# 从各个子文件导入视图类并导出
from .select_views import ProcurementSelectView, ProcurementPurchasingListView
from .progress_views import ProcurementProgressView

# 导出所有视图类
__all__ = [
    'ProcurementSelectView',
    'ProcurementPurchasingListView',
    'ProcurementProgressView',
]
