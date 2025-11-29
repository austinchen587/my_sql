# emall_purchasing/views/__init__.py
from .select_views import ProcurementSelectView, ProcurementPurchasingListView
from .progress_views import ProcurementProgressView, update_purchasing_info
from .supplier_views import add_supplier_to_procurement, delete_supplier, update_supplier
from .remark_views import add_remark

__all__ = [
    'ProcurementSelectView',
    'ProcurementPurchasingListView',
    'ProcurementProgressView',
    'update_purchasing_info',
    'add_supplier_to_procurement',
    'delete_supplier',
    'update_supplier',
    'add_remark',
]
