# emall_purchasing/serializers.py
from rest_framework import serializers
from .models import ProcurementPurchasing, ProcurementRemark, Supplier, SupplierCommodity, ProcurementSupplier, UnifiedProcurementRemark
from emall.models import ProcurementEmall  # 从emall应用导入

class SupplierCommoditySerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierCommodity
        fields = ['id', 'name', 'specification', 'price', 'quantity', 'product_url']

class SupplierSerializer(serializers.ModelSerializer):
    commodities = SupplierCommoditySerializer(many=True, read_only=True)
    total_quote = serializers.SerializerMethodField()
    
    class Meta:
        model = Supplier
        fields = ['id', 'name', 'source', 'contact', 'store_name', 'commodities', 'total_quote']
    
    def get_total_quote(self, obj):
        total = 0
        for commodity in obj.commodities.all():
            total += commodity.price * commodity.quantity
        return total

class ProcurementSupplierSerializer(serializers.ModelSerializer):
    supplier = SupplierSerializer(read_only=True)
    total_quote = serializers.ReadOnlyField(source='get_total_quote')
    
    class Meta:
        model = ProcurementSupplier
        fields = ['id', 'supplier', 'is_selected', 'total_quote']

class ProcurementRemarkSerializer(serializers.ModelSerializer):
    created_at_display = serializers.DateTimeField(source='created_at', format='%Y-%m-%d %H:%M', read_only=True)
    
    class Meta:
        model = ProcurementRemark
        fields = ['id', 'remark_content', 'created_by', 'created_at', 'created_at_display']

class UnifiedProcurementRemarkSerializer(serializers.ModelSerializer):
    """统一采购备注序列化器"""
    created_at_display = serializers.SerializerMethodField()
    remark_type_display = serializers.CharField(source='get_remark_type_display', read_only=True)
    procurement_title = serializers.CharField(source='procurement.project_title', read_only=True)
    procurement_number = serializers.CharField(source='procurement.project_number', read_only=True)
    
    class Meta:
        model = UnifiedProcurementRemark
        fields = [
            'id', 'procurement', 'procurement_title', 'procurement_number',
            'remark_content', 'created_by', 'remark_type', 'remark_type_display',
            'purchasing', 'created_at', 'created_at_display', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_created_at_display(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S') if obj.created_at else ''

class ProcurementPurchasingSerializer(serializers.ModelSerializer):
    procurement_title = serializers.CharField(source='procurement.project_title', read_only=True)
    procurement_number = serializers.CharField(source='procurement.project_number', read_only=True)
    total_budget = serializers.SerializerMethodField()
    suppliers_info = serializers.SerializerMethodField()
    bidding_status_display = serializers.CharField(source='get_bidding_status_display', read_only=True)
    remarks_history = ProcurementRemarkSerializer(many=True, read_only=True)
    project_owner = serializers.CharField(read_only=True)
    
    class Meta:
        model = ProcurementPurchasing
        fields = [
            'id', 'procurement_id', 'is_selected', 'bidding_status', 'bidding_status_display',
            'client_contact', 'client_phone', 'procurement_title', 'procurement_number',
            'total_budget', 'suppliers_info', 'remarks_history', 'created_at', 'updated_at',
            'project_owner'
        ]
    
    def get_total_budget(self, obj):
        return obj.get_total_budget()
    
    def get_suppliers_info(self, obj):
        return obj.get_suppliers_info()
