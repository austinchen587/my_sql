# emall_purchasing/views/base_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import ProcurementPurchasing
import logging

logger = logging.getLogger(__name__)

class BaseProcurementView(APIView):
    """采购视图基类"""
    
    def get_procurement_object(self, procurement_id):
        """获取采购对象，带异常处理"""
        try:
            return ProcurementPurchasing.objects.select_related(
                'procurement'
            ).prefetch_related(
                'suppliers',
                'suppliers__commodities',
                'remarks_history'
            ).get(procurement_id=procurement_id)
        except ProcurementPurchasing.DoesNotExist:
            logger.error(f"采购项目不存在，ID: {procurement_id}")
            return None  # 修复这里的语法错误
