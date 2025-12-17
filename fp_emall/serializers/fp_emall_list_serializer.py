# fp_emall/serializers/fp_emall_list_serializer.py
from rest_framework import serializers

class FpEmallSerializer(serializers.Serializer):
    """FP Emall 数据序列化器"""
    
    # 基础字段
    fp_id = serializers.IntegerField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    
    # 字符型字段
    fp_total_price_control = serializers.CharField(allow_blank=True, allow_null=True)
    fp_publish_date = serializers.CharField(allow_blank=True, allow_null=True)
    fp_purchasing_unit = serializers.CharField(allow_blank=True, allow_null=True)
    fp_url = serializers.CharField(allow_blank=True, allow_null=True)
    fp_project_title = serializers.CharField(allow_blank=True, allow_null=True)
    fp_project_number = serializers.CharField(allow_blank=True, allow_null=True)
    fp_quote_start_time = serializers.CharField(allow_blank=True, allow_null=True)
    fp_quote_end_time = serializers.CharField(allow_blank=True, allow_null=True)
    fp_region = serializers.CharField(allow_blank=True, allow_null=True)
    fp_project_name = serializers.CharField(allow_blank=True, allow_null=True)
    
    # 数组字段
    fp_commodity_names = serializers.ListField(
        child=serializers.CharField(allow_blank=True), 
        allow_null=True, 
        allow_empty=True
    )
    fp_parameter_requirements = serializers.ListField(
        child=serializers.CharField(allow_blank=True), 
        allow_null=True, 
        allow_empty=True
    )
    fp_purchase_quantities = serializers.ListField(
        child=serializers.CharField(allow_blank=True), 
        allow_null=True, 
        allow_empty=True
    )
    fp_control_amounts = serializers.ListField(
        child=serializers.CharField(allow_blank=True), 
        allow_null=True, 
        allow_empty=True
    )
    fp_suggested_brands = serializers.ListField(
        child=serializers.CharField(allow_blank=True), 
        allow_null=True, 
        allow_empty=True
    )
    fp_business_items = serializers.ListField(
        child=serializers.CharField(allow_blank=True), 
        allow_null=True, 
        allow_empty=True
    )
    fp_business_requirements = serializers.ListField(
        child=serializers.CharField(allow_blank=True), 
        allow_null=True, 
        allow_empty=True
    )
    fp_related_links = serializers.ListField(
        child=serializers.CharField(allow_blank=True), 
        allow_null=True, 
        allow_empty=True
    )
    fp_download_files = serializers.ListField(
        child=serializers.CharField(allow_blank=True), 
        allow_null=True, 
        allow_empty=True
    )
    
    # 计算字段（用于排序，不保存到数据库）
    converted_price = serializers.FloatField(allow_null=True)
