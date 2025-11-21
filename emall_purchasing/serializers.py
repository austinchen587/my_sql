from rest_framework import serializers
from .models import ProcurementPurchasing, ProcurementRemark

class ProcurementRemarkSerializer(serializers.ModelSerializer):
    """采购备注序列化器"""
    created_at_display = serializers.CharField(source='created_at', read_only=True)
    
    class Meta:
        model = ProcurementRemark
        fields = ['id', 'remark_content', 'created_by', 'created_at', 'created_at_display']

class ProcurementPurchasingSerializer(serializers.ModelSerializer):
    procurement_title = serializers.CharField(source='procurement.project_title', read_only=True)
    procurement_url = serializers.CharField(source='procurement.url', read_only=True)
    quote_end_time = serializers.CharField(source='procurement.quote_end_time', read_only=True)
    
    # 新增的计算字段
    commodities_count = serializers.ReadOnlyField(source='get_commodities_count')
    total_amount = serializers.ReadOnlyField(source='get_total_amount')
    commodities_info = serializers.ReadOnlyField(source='get_commodities_info')
    
    # 竞标状态显示名称
    bidding_status_display = serializers.CharField(
        source='get_bidding_status_display', 
        read_only=True
    )
    
    # 备注历史
    remarks_history = ProcurementRemarkSerializer(many=True, read_only=True)
    
    class Meta:
        model = ProcurementPurchasing
        fields = [
            'id', 'procurement_id', 'is_selected', 
            
            # 商品相关字段
            'commodity_names', 'product_specifications', 'prices', 
            'quantities', 'product_urls', 'bidding_status', 'remarks',
            
            # 采购进度字段
            'client_contact', 'client_phone', 'supplier_source',
            'supplier_store', 'supplier_contact', 'cost',
            
            # 从关联模型获取的字段
            'procurement_title', 'procurement_url', 'quote_end_time',
            
            # 计算字段和显示字段
            'commodities_count', 'total_amount', 'commodities_info',
            'bidding_status_display',
            
            # 备注历史
            'remarks_history',
            
            'created_at', 'updated_at'
        ]
