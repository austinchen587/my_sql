from rest_framework import serializers
from .models import ProcurementPurchasing, ProcurementRemark, Supplier, SupplierCommodity, ProcurementSupplier

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

class ProcurementPurchasingSerializer(serializers.ModelSerializer):
    procurement_title = serializers.CharField(source='procurement.project_title', read_only=True)
    procurement_number = serializers.CharField(source='procurement.project_number', read_only=True)
    total_budget = serializers.SerializerMethodField()
    suppliers_info = serializers.SerializerMethodField()
    bidding_status_display = serializers.CharField(source='get_bidding_status_display', read_only=True)
    remarks_history = ProcurementRemarkSerializer(many=True, read_only=True)
    
    class Meta:
        model = ProcurementPurchasing
        fields = [
            'id', 'procurement_id', 'is_selected', 'bidding_status', 'bidding_status_display',
            'client_contact', 'client_phone', 'procurement_title', 'procurement_number',
            'total_budget', 'suppliers_info', 'remarks_history', 'created_at', 'updated_at'
        ]
    
    def get_total_budget(self, obj):
        return obj.get_total_budget()
    
    def get_suppliers_info(self, obj):
        return obj.get_suppliers_info()
