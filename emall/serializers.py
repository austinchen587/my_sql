# emall/serializers.py
from rest_framework import serializers
from .models import ProcurementEmall
from emall_purchasing.models import ProcurementPurchasing
from emall_purchasing.serializers import ProcurementPurchasingSerializer

class ProcurementEmallSerializer(serializers.ModelSerializer):
    # 添加跨表字段
    is_selected = serializers.SerializerMethodField()
    bidding_status = serializers.SerializerMethodField()
    bidding_status_display = serializers.SerializerMethodField()
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
            'url', 'created_at', 'updated_at',
            # 跨表字段
            'is_selected', 'bidding_status', 'bidding_status_display', 'purchasing_info'
        ]
    
    def get_is_selected(self, obj):
        """从采购进度表获取选中状态"""
        print(f"\n🎯 开始序列化项目 {obj.id} - {obj.project_title}")
        
        # 检查上下文
        context_keys = list(self.context.keys())
        print(f"🔍 序列化器上下文包含: {context_keys}")
        
        purchasing_info_map = self.context.get('purchasing_info_map', {})
        print(f"📊 映射表大小: {len(purchasing_info_map)}")
        print(f"📋 映射表包含项目 {obj.id}: {obj.id in purchasing_info_map}")
        
        if obj.id in purchasing_info_map:
            info = purchasing_info_map[obj.id]
            result = info.is_selected
            print(f"✅ 从映射表获取项目 {obj.id} 的 is_selected: {result}")
            print(f"📝 采购信息对象: {info}")
            return result
        else:
            print(f"⚠️  项目 {obj.id} 不在映射表中，直接查询数据库")
            try:
                purchasing_info = ProcurementPurchasing.objects.filter(
                    procurement_id=obj.id
                ).first()
                if purchasing_info:
                    result = purchasing_info.is_selected
                    print(f"🔍 数据库查询结果: is_selected={result}")
                else:
                    result = False
                    print(f"🔍 数据库查询结果: 无采购信息记录")
                return result
            except Exception as e:
                print(f"❌ 数据库查询错误: {e}")
                return False
    
    def get_bidding_status(self, obj):
        """获取招标状态"""
        try:
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
