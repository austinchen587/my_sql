# supplier_management/views.py
"""
主视图文件 - 保持向后兼容性
所有视图函数已拆分到 views/ 目录下
"""

# 从拆分后的模块导入所有视图函数
from .views import (
    project_list,
    get_project_suppliers,
    toggle_supplier_selection,
    update_supplier,
    add_supplier,
    delete_supplier
)

# 导出所有函数，确保外部引用不受影响
__all__ = [
    'project_list',
 '__get_project_suppliers',
    'toggle_supplier_selection',
    'update_supplier',
    'add_supplier',
    'delete_supplier',
]
