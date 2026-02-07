# supplier_management/views/__init__.py

# 1. 从 project_views 导入项目相关的函数
from .project_views import (
    project_list,
    project_list_success,
    get_project_suppliers  # <--- 这个必须在这里，因为它在 project_views.py 里
)

# 2. 从 supplier_views 导入供应商相关的函数
from .supplier_views import (
    toggle_supplier_selection,
    update_supplier,
    add_supplier,
    delete_supplier
)

# 3. 导出所有函数
__all__ = [
    'project_list',
    'project_list_success',
    'get_project_suppliers',
    'toggle_supplier_selection',
    'update_supplier',
    'add_supplier',
    'delete_supplier',
]