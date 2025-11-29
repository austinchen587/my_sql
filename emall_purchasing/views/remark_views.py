# emall_purchasing/views/remark_views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from ..models import ProcurementPurchasing, ProcurementRemark
from .utils import safe_json_loads
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
def add_remark(request, procurement_id):
    """添加备注"""
    try:
        logger.info(f"开始添加备注，采购项目ID: {procurement_id}")
        purchasing_info = ProcurementPurchasing.objects.get(procurement_id=procurement_id)
        data = safe_json_loads(request)
        
        if not data:
            return Response({'error': '无效的JSON数据'}, status=status.HTTP_400_BAD_REQUEST)
        
        remark_content = data.get('remark_content', '').strip()
        created_by = data.get('created_by', '').strip()
        
        if not remark_content or not created_by:
            return Response({'error': '备注内容和创建人不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        
        new_remark = ProcurementRemark.objects.create(
            purchasing=purchasing_info,
            remark_content=remark_content,
            created_by=created_by
        )
        
        logger.info(f"成功添加备注，ID: {new_remark.id}")
        return Response({'success': True, 'message': '备注添加成功', 'remark_id': new_remark.id})
        
    except ProcurementPurchasing.DoesNotExist:
        logger.error(f"采购项目不存在，ID: {procurement_id}")
        return Response({'error': '采购项目不存在'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"添加备注失败，错误: {str(e)}", exc_info=True)
        return Response({'error': f'添加失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
