# emall_purchasing/admin.py
from django.contrib import admin
from .models import Supplier, SupplierCommodity, ProcurementPurchasing, ProcurementSupplier, ProcurementRemark, UnifiedProcurementRemark
@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'source', 'contact', 'store_name', 'purchaser_created_by', 'purchaser_created_at']
    list_filter = ['purchaser_created_role', 'source']
    search_fields = ['name', 'store_name']
@admin.register(SupplierCommodity)
class SupplierCommodityAdmin(admin.ModelAdmin):
    list_display = ['name', 'supplier', 'price', 'quantity', 'purchaser_created_by', 'purchaser_created_at']
    list_filter = ['purchaser_created_role']
    search_fields = ['name', 'supplier__name']
@admin.register(ProcurementSupplier)
class ProcurementSupplierAdmin(admin.ModelAdmin):
    list_display = ['procurement', 'supplier', 'is_selected', 'purchaser_created_by', 'purchaser_created_at']
    list_filter = ['is_selected', 'purchaser_created_role']
    search_fields = ['procurement__procurement__project_title', 'supplier__name']