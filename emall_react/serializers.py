# emall_react/serializers.py
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
            'total_price_control',
            'total_price_numeric',  # 添加数字化字段
            'quote_start_time', 
            'quote_end_time',
            'url',  # 添加url字段
        ]
        read_only_fields = fields
    
    def get_total_price_numeric(self, obj):
        """
        将total_price_control转换为数字
        规则：
        - 如果包含"万元"且不包含"元万元"：数值 × 10000
        - 如果包含"元万元"：直接取数值部分
        """
        price_str = obj.total_price_control
        if not price_str:
            return None
            
        try:
            # 清理字符串，去除空格等
            price_str = str(price_str).strip()
            
            # 提取数字部分（支持小数和整数，包含逗号分隔符）
            match = re.search(r'([\d,]+(?:\.\d+)?)', price_str.replace(',', ''))
            if not match:
                return None
                
            number = float(match.group(1).replace(',', ''))
            
            # 判断单位类型
            if '元万元' in price_str:
                # 情况1：包含"元万元"，直接取数值
                return round(number, 2)
            elif '万元' in price_str:
                # 情况2：包含"万元"，数值 × 10000
                return round(number * 10000, 2)
            else:
                # 其他情况返回None或原数值（根据需求调整）
                return None
                
        except (ValueError, TypeError, AttributeError):
            return None
