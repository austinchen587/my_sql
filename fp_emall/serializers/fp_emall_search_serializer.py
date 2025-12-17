# fp_emall/serializers/fp_emall_search_serializer.py
from rest_framework import serializers

class FpEmallSearchSerializer(serializers.Serializer):
    """FP Emall 搜索数据序列化器"""
    
    fp_project_name = serializers.CharField()
    fp_project_number = serializers.CharField()
    fp_purchasing_unit = serializers.CharField()
    fp_total_price_control = serializers.CharField()
    converted_price = serializers.FloatField(allow_null=True)
    fp_quote_start_time = serializers.CharField()
    fp_quote_end_time = serializers.CharField()
