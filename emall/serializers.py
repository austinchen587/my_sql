# emall/serializers.py
from rest_framework import serializers
from .models import ProcurementEmall
from emall_purchasing.models import ProcurementPurchasing
from emall_purchasing.serializers import ProcurementPurchasingSerializer
import json
import ast

class ProcurementEmallSerializer(serializers.ModelSerializer):
    # 为所有数组字段添加自定义序列化方法
    commodity_names = serializers.SerializerMethodField()
    parameter_requirements = serializers.SerializerMethodField()
    purchase_quantities = serializers.SerializerMethodField()
    control_amounts = serializers.SerializerMethodField()
    suggested_brands = serializers.SerializerMethodField()
    business_items = serializers.SerializerMethodField()
    business_requirements = serializers.SerializerMethodField()
    related_links = serializers.SerializerMethodField()
    download_files = serializers.SerializerMethodField()

     # 新增字段
    project_owner = serializers.SerializerMethodField()
    is_selected = serializers.SerializerMethodField()
    bidding_status = serializers.SerializerMethodField()
    bidding_status_display = serializers.SerializerMethodField()
    
    def _flatten_array(self, value):
        """展平双重嵌套的数组"""
        if value is None:
            return []
        
        # 如果已经是单层列表，直接返回
        if isinstance(value, list):
            # 检查是否是双重嵌套 [[item1], [item2]]
            if value and isinstance(value[0], list):
                # 展平双重嵌套
                flattened = []
                for sublist in value:
                    if isinstance(sublist, list):
                        flattened.extend(sublist)
                    else:
                        flattened.append(sublist)
                return flattened
            else:
                return value
        
        # 如果是字符串或其他类型，包装成列表
        return [value] if value else []
    
    
    def get_commodity_names(self, obj):
        return self._flatten_array(obj.commodity_names)
    
    def get_parameter_requirements(self, obj):
        return self._flatten_array(obj.parameter_requirements)
    
    def get_purchase_quantities(self, obj):
        return self._flatten_array(obj.purchase_quantities)
    
    def get_control_amounts(self, obj):
        return self._flatten_array(obj.control_amounts)
    
    def get_suggested_brands(self, obj):
        return self._flatten_array(obj.suggested_brands)
    
    def get_business_items(self, obj):
        return self._flatten_array(obj.business_items)
    
    def get_business_requirements(self, obj):
        return self._flatten_array(obj.business_requirements)
    
    def get_related_links(self, obj):
        return self._flatten_array(obj.related_links)
    
    def get_download_files(self, obj):
        return self._flatten_array(obj.download_files)
    def get_project_owner(self, obj):
        """从 ProcurementPurchasing 获取项目归属人"""
        try:
            print(f"🔍 序列化器调试 - 项目ID: {obj.id}")
            
            purchasing_info = self.context.get('purchasing_info')
            if purchasing_info:
                print(f"🔍 从purchasing_info获取: {purchasing_info.project_owner}")
                return purchasing_info.project_owner
            
            purchasing_info_map = self.context.get('purchasing_info_map', {})
            if obj.id in purchasing_info_map:
                owner = purchasing_info_map[obj.id].project_owner
                print(f"🔍 从purchasing_info_map获取: {owner}")
                return owner
            
            purchasing_info = ProcurementPurchasing.objects.filter(
                procurement_id=obj.id
            ).first()
            owner = purchasing_info.project_owner if purchasing_info else '未分配'
            print(f"🔍 从数据库查询获取: {owner}")
            return owner
            
        except Exception as e:
            print(f"❌ 获取project_owner错误: {e}")
        return '未分配'
    
    
    
    total_price_numeric = serializers.SerializerMethodField()
    
    def get_total_price_numeric(self, obj):
        from .views_list.utils import convert_price_to_number
        return convert_price_to_number(obj.total_price_control)
    class Meta:
        model = ProcurementEmall
        fields = [
            'id', 'created_at', 'updated_at', 'total_price_control',
            'publish_date', 'purchasing_unit', 'url', 'project_title',
            'project_number', 'quote_start_time', 'quote_end_time',
            'region', 'project_name', 'commodity_names', 
            'parameter_requirements', 'purchase_quantities', 
            'control_amounts', 'suggested_brands', 'business_items',
            'business_requirements', 'related_links', 'download_files',
            'total_price_numeric','project_owner',
            'is_selected', 'bidding_status', 'bidding_status_display'
        ]
    
    def to_representation(self, instance):
        """重写以确保数据格式正确"""
        data = super().to_representation(instance)
        
        # 调试输出
        print(f"\n🔍 调试信息 - 项目 {instance.id}:")
        print(f"commodity_names: {data.get('commodity_names')}")
        print(f"parameter_requirements: {data.get('parameter_requirements')}")
        print(f"business_items: {data.get('business_items')}")
        print(f"business_requirements: {data.get('business_requirements')}")
        print(f"related_links: {data.get('related_links')}")
        print(f"download_files: {data.get('download_files')}")
        
        return data

    
    def get_total_price_numeric(self, obj):
        """获取数值格式的价格"""
        from .views_list.utils import convert_price_to_number
        return convert_price_to_number(obj.total_price_control)
    
    def get_is_selected(self, obj):
        """从采购进度表获取选中状态"""
        try:
            # 首先检查上下文中的 purchasing_info
            purchasing_info = self.context.get('purchasing_info')
            if purchasing_info:
                return purchasing_info.is_selected
            
            # 如果没有，检查映射表
            purchasing_info_map = self.context.get('purchasing_info_map', {})
            if obj.id in purchasing_info_map:
                return purchasing_info_map[obj.id].is_selected
            
            # 最后查询数据库
            purchasing_info = ProcurementPurchasing.objects.filter(
                procurement_id=obj.id
            ).first()
            return purchasing_info.is_selected if purchasing_info else False
        except Exception:
            return False
    
    def get_bidding_status(self, obj):
        """获取招标状态"""
        try:
            purchasing_info = self.context.get('purchasing_info')
            if purchasing_info:
                return purchasing_info.bidding_status
            
            purchasing_info_map = self.context.get('purchasing_info_map', {})
            if obj.id in purchasing_info_map:
                return purchasing_info_map[obj.id].bidding_status
            
            purchasing_info = ProcurementPurchasing.objects.filter(
                procurement_id=obj.id
            ).first()
            return purchasing_info.bidding_status if purchasing_info else 'not_started'
        except Exception:
            return 'not_started'
    
    def get_bidding_status_display(self, obj):
        """获取招标状态显示文本"""
        try:
            purchasing_info = self.context.get('purchasing_info')
            if purchasing_info:
                return purchasing_info.get_bidding_status_display()
            
            purchasing_info_map = self.context.get('purchasing_info_map', {})
            if obj.id in purchasing_info_map:
                return purchasing_info_map[obj.id].get_bidding_status_display()
            
            purchasing_info = ProcurementPurchasing.objects.filter(
                procurement_id=obj.id
            ).first()
            if purchasing_info:
                return purchasing_info.get_bidding_status_display()
            return '未开始'
        except Exception:
            return '未开始'
    
    def get_purchasing_info(self, obj):
        """获取完整的采购进度信息"""
        try:
            purchasing_info = self.context.get('purchasing_info')
            if purchasing_info:
                return ProcurementPurchasingSerializer(purchasing_info).data
            
            purchasing_info_map = self.context.get('purchasing_info_map', {})
            if obj.id in purchasing_info_map:
                return ProcurementPurchasingSerializer(
                    purchasing_info_map[obj.id]
                ).data
            
            purchasing_info = ProcurementPurchasing.objects.filter(
                procurement_id=obj.id
            ).first()
            if purchasing_info:
                return ProcurementPurchasingSerializer(purchasing_info).data
            return None
        except Exception as e:
            print(f"❌ 获取purchasing_info错误: {e}")
            return None
