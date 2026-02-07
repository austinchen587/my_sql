# supplier_management/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('projects/', views.project_list, name='project-list'),
    path('projects-success/', views.project_list_success, name='project-list-success'),
    path('project-suppliers/', views.get_project_suppliers, name='project-suppliers'),
    path('suppliers/toggle-selection/', views.toggle_supplier_selection, name='toggle-supplier-selection'),
    path('suppliers/update/', views.update_supplier, name='update-supplier'),
    path('suppliers/add/', views.add_supplier, name='add-supplier'),
    path('suppliers/delete/', views.delete_supplier, name='delete-supplier'),
    
    # [删除] 下面这行必须删掉，因为 views.import_ai_suppliers 已经不存在了
    # path('suppliers/import-ai/', views.import_ai_suppliers, name='import-ai-suppliers'),
]