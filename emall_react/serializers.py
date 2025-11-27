from rest_framework import serializers
from emall.models import ProcurementEmall

class EmallListSerializer(serializers.ModelSerializer):
    """
    采购项目列表序列化器
    """
    class Meta:
        model = ProcurementEmall
        fields = [
            'id', 
            'project_title', 
            'purchasing_unit', 
            'publish_date',
            'region', 
            'project_name', 
            'commodity_names', 
            'total_price_control',
            'quote_start_time', 
            'quote_end_time',
            # ... 添加其他你需要的字段
        ]
        read_only_fields = fields
