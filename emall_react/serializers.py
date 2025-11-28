# emall_react/serializers.py - 添加完整字段
from rest_framework import serializers
from emall.models import ProcurementEmall
import re

class EmallListSerializer(serializers.ModelSerializer):
    """
    采购项目列表序列化器
    在序列化时对total_price_control进行数字化处理
    """
    total_price_numeric = serializers.SerializerMethodField()
    
    class Meta:
        model = ProcurementEmall
        fields = [
            'id', 
            'project_title', 
            'purchasing_unit', 
            'publish_date',
            'region', 
            'project_name', 
            'project_number',
            'commodity_names', 
            'parameter_requirements',
            'purchase_quantities',
            'control_amounts',
            'suggested_brands',
            'business_items',
            'business_requirements',
            'related_links',
            'download_files',
            'total_price_control',
            'total_price_numeric',
            'quote_start_time', 
            'quote_end_time',
            'url',
        ]
        read_only_fields = fields
    
    def get_total_price_numeric(self, obj):
        """
        将total_price_control转换为数字
        """
        price_str = obj.total_price_control
        if not price_str:
            return None
            
        try:
            price_str = str(price_str).strip()
            match = re.search(r'([\d,]+(?:\.\d+)?)', price_str.replace(',', ''))
            if not match:
                return None
                
            number = float(match.group(1).replace(',', ''))
            
            if '元万元' in price_str:
                return round(number, 2)
            elif '万元' in price_str:
                return round(number * 10000, 2)
            else:
                return None
                
        except (ValueError, TypeError, AttributeError):
            return None
