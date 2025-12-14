# supplier_management/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('projects/', views.project_list, name='project-list'),
    path('projects-success/', views.project_list_success, name='project-list-success'),  # 新增
    path('project-suppliers/', views.get_project_suppliers, name='project-suppliers'),
    path('suppliers/toggle-selection/', views.toggle_supplier_selection, name='toggle-supplier-selection'),
    path('suppliers/update/', views.update_supplier, name='update-supplier'),
    path('suppliers/add/', views.add_supplier, name='add-supplier'),
    path('suppliers/delete/', views.delete_supplier, name='delete-supplier'),
]
