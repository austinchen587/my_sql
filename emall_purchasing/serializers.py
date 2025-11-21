from rest_framework import serializers
from .models import ProcurementPurchasing

class ProcurementPurchasingSerializer(serializers.ModelSerializer):
    procurement_title = serializers.CharField(source='procurement.project_title', read_only=True)
    procurement_url = serializers.CharField(source='procurement.url', read_only=True)
    quote_end_time = serializers.CharField(source='procurement.quote_end_time', read_only=True)
    
    class Meta:
        model = ProcurementPurchasing
        fields = [
            'id', 'procurement_id', 'is_selected', 
            'client_contact', 'client_phone', 'supplier_source',
            'supplier_store', 'supplier_contact', 'cost',
            'created_at', 'updated_at',
            'procurement_title', 'procurement_url', 'quote_end_time'  # 从关联模型获取的字段
        ]
