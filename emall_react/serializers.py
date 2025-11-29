# emall_react/serializers.py
from rest_framework import serializers
from emall.models import ProcurementEmall
from emall_purchasing.models import ProcurementPurchasing
from .utils import get_numeric_price_for_item

class EmallListSerializer(serializers.ModelSerializer):
    """采购项目列表序列化器"""
    is_selected = serializers.SerializerMethodField()
    bidding_status = serializers.SerializerMethodField()
    bidding_status_display = serializers.SerializerMethodField()
    purchasing_info = serializers.SerializerMethodField()
    total_price_numeric = serializers.SerializerMethodField()  # 新增数字价格字段
    
    class Meta:
        model = ProcurementEmall
        fields = [
            'id', 'project_title', 'project_number', 'purchasing_unit',
            'total_price_control', 'total_price_numeric', 'publish_date', 'quote_end_time',  # 添加数字价格
            'project_name', 'region', 'commodity_names', 'quote_start_time', 'url',
            'is_selected', 'bidding_status', 'bidding_status_display', 'purchasing_info'
        ]
    
    def get_is_selected(self, obj):
        """从采购进度表获取选中状态"""
        try:
            purchasing_info = ProcurementPurchasing.objects.filter(
                procurement_id=obj.id
            ).first()
            return purchasing_info.is_selected if purchasing_info else False
        except Exception:
            return False
    
    def get_bidding_status(self, obj):
        """获取投标状态"""
        try:
            purchasing_info = ProcurementPurchasing.objects.filter(
                procurement_id=obj.id
            ).first()
            return purchasing_info.bidding_status if purchasing_info else 'not_started'
        except Exception:
            return 'not_started'
    
    def get_bidding_status_display(self, obj):
        """获取投标状态显示文本"""
        status_mapping = {
            'not_started': '未开始',
            'in_progress': '进行中',
            'successful': '成功',
            'failed': '失败',
            'cancelled': '已取消'
        }
        status = self.get_bidding_status(obj)
        return status_mapping.get(status, '未知')
    
    def get_purchasing_info(self, obj):
        """获取采购信息"""
        try:
            purchasing_info = ProcurementPurchasing.objects.filter(
                procurement_id=obj.id
            ).first()
            if purchasing_info:
                return {
                    'suppliers': purchasing_info.suppliers,
                    'progress_notes': purchasing_info.progress_notes,
                    'updated_at': purchasing_info.updated_at
                }
            return None
        except Exception:
            return None
    
    def get_total_price_numeric(self, obj):
        """获取数字化的价格"""
        return get_numeric_price_for_item(obj)
