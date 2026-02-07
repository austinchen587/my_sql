# supplier_management/views.py

# 1. 从 project_views 导入项目相关视图
from .views.project_views import (
    project_list,
    project_list_success,
    get_project_suppliers
)

# 2. 从 supplier_views 导入供应商操作视图
from .views.supplier_views import (
    toggle_supplier_selection,
    update_supplier,
    add_supplier,
    delete_supplier
)

# 3. 导出所有函数
__all__ = [
    'project_list',
    'project_list_success',
    'get_project_suppliers', # [修复] 修正了之前的 typo (去掉了前面的下划线)
    'toggle_supplier_selection',
    'update_supplier',
    'add_supplier',
    'delete_supplier',
]