# emall/serializers.py
from rest_framework import serializers
from emall.models import ProcurementEmall
from emall_purchasing.models import ProcurementPurchasing
from emall_purchasing.serializers import ProcurementPurchasingSerializer

class ProcurementEmallSerializer(serializers.ModelSerializer):
    is_selected = serializers.SerializerMethodField()
    purchasing_info = serializers.SerializerMethodField()
    
    class Meta:
        model = ProcurementEmall
        fields = [
            'id', 'project_title', 'purchasing_unit', 'region', 
            'total_price_control', 'publish_date', 'quote_end_time',
            'project_number', 'quote_start_time', 'project_name',
            'commodity_names', 'parameter_requirements', 'purchase_quantities',
            'control_amounts', 'suggested_brands', 'business_items',
            'business_requirements', 'related_links', 'download_files',
            'url', 'created_at', 'updated_at', 'is_selected', 'purchasing_info'
        ]
    
    def get_is_selected(self, obj):
        """获取是否选中状态"""
        try:
            # 从上下文获取采购信息映射
            purchasing_info_map = self.context.get('purchasing_info_map', {})
            
            # 如果有采购信息且被选中
            if obj.id in purchasing_info_map:
                return purchasing_info_map[obj.id].is_selected
            
            # 如果上下文中有单个采购信息对象
            purchasing_info = self.context.get('purchasing_info')
            if purchasing_info and purchasing_info.procurement_id == obj.id:
                return purchasing_info.is_selected
                
            return False
        except Exception:
            return False
    
    def get_purchasing_info(self, obj):
        """获取采购进度信息"""
        try:
            purchasing_info_map = self.context.get('purchasing_info_map', {})
            
            if obj.id in purchasing_info_map:
                return ProcurementPurchasingSerializer(
                    purchasing_info_map[obj.id]
                ).data
            
            purchasing_info = self.context.get('purchasing_info')
            if purchasing_info and purchasing_info.procurement_id == obj.id:
                return ProcurementPurchasingSerializer(purchasing_info).data
                
            return None
        except Exception:
            return None
