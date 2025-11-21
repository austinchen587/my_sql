from .views_list.base_views import ProcurementListView
from .views_list.data_views import ProcurementListDataView, ProcurementDetailView
# 保持原有的类名导出，确保URLs不需要修改
__all__ = [
    'ProcurementListView',
    'ProcurementListDataView',
    'ProcurementDetailView',
]