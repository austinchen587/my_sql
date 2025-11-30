# emall_react/serializers.py
from rest_framework import serializers
from emall.models import ProcurementEmall
from emall_purchasing.models import ProcurementPurchasing, ProcurementRemark, ProcurementSupplier, Supplier
from .utils import get_numeric_price_for_item

class EmallListSerializer(serializers.ModelSerializer):
    """采购项目列表序列化器"""
    is_selected = serializers.SerializerMethodField()
    bidding_status = serializers.SerializerMethodField()
    bidding_status_display = serializers.SerializerMethodField()
    purchasing_info = serializers.SerializerMethodField()
    total_price_numeric = serializers.SerializerMethodField()
    latest_remark = serializers.SerializerMethodField()
    project_owner = serializers.SerializerMethodField()
    suppliers_count = serializers.SerializerMethodField()  # 新增：供应商数量
    
    class Meta:
        model = ProcurementEmall
        fields = [
            'id', 'project_title', 'project_number', 'purchasing_unit',
            'total_price_control', 'total_price_numeric', 'publish_date', 'quote_end_time',
            'project_name', 'region', 'commodity_names', 'quote_start_time', 'url',
            'is_selected', 'bidding_status', 'bidding_status_display', 'purchasing_info',
            'latest_remark', 'project_owner', 'suppliers_count','project_owner'
        ]

    def get_project_owner(self, obj):
        """获取项目归属人"""
        try:
            purchasing_info = obj.purchasing_info
            if purchasing_info and purchasing_info.project_owner:
                return purchasing_info.project_owner
            return '未分配'
        except ProcurementPurchasing.DoesNotExist:
            return '未分配'
        except Exception:
            return '未分配'
    
    def get_is_selected(self, obj):
        """从采购进度表获取选中状态"""
        try:
            # 使用 try-except 避免对象不存在时的错误
            purchasing_info = obj.purchasing_info
            return purchasing_info.is_selected if purchasing_info else False
        except ProcurementPurchasing.DoesNotExist:
            return False
        except Exception:
            return False
    
    def get_bidding_status(self, obj):
        """获取投标状态"""
        try:
            purchasing_info = obj.purchasing_info
            return purchasing_info.bidding_status if purchasing_info else 'not_started'
        except ProcurementPurchasing.DoesNotExist:
            return 'not_started'
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
            purchasing_info = obj.purchasing_info
            if purchasing_info:
                return {
                    'suppliers': purchasing_info.suppliers.count() if hasattr(purchasing_info, 'suppliers') else 0,
                    'updated_at': purchasing_info.updated_at.isoformat() if purchasing_info.updated_at else ''
                }
            return None
        except ProcurementPurchasing.DoesNotExist:
            return None
        except Exception:
            return None
    
    def get_total_price_numeric(self, obj):
        """获取数字化的价格"""
        return get_numeric_price_for_item(obj)
    
    def get_latest_remark(self, obj):
        """获取最新备注信息"""
        try:
            purchasing_info = obj.purchasing_info
            if purchasing_info:
                # 获取最新备注
                latest_remark = purchasing_info.remarks_history.order_by('-created_at').first()
                if latest_remark:
                    return {
                        'content': latest_remark.remark_content or '',
                        'created_by': latest_remark.created_by or '',
                        'created_at': latest_remark.created_at.isoformat() if latest_remark.created_at else ''
                    }
            return None
        except ProcurementPurchasing.DoesNotExist:
            return None
        except Exception:
            return None
    
    def get_suppliers_count(self, obj):
        """获取供应商数量"""
        try:
            purchasing_info = obj.purchasing_info
            if purchasing_info:
                return purchasing_info.suppliers.count()
            return 0
        except ProcurementPurchasing.DoesNotExist:
            return 0
        except Exception:
            return 0
