# emall_purchasing/views/remark_views.py
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from ..models import ProcurementPurchasing, ProcurementRemark
from .utils import safe_json_loads
import logging
from urllib.parse import unquote # [核心修复 1] 引入 URL 解码库

logger = logging.getLogger(__name__)

@api_view(['POST'])
@authentication_classes([]) # 保持禁用以跳过CSRF
@permission_classes([AllowAny]) 
def add_remark(request, procurement_id):
    try:
        logger.info(f"开始添加备注，采购项目ID: {procurement_id}")
        purchasing_info = ProcurementPurchasing.objects.get(procurement_id=procurement_id)
        data = safe_json_loads(request)
        
        if not data:
            return Response({'error': '无效的JSON数据'}, status=status.HTTP_400_BAD_REQUEST)
        
        remark_content = data.get('remark_content', '').strip()
        
        # 🌟 终极修复：优先直接从前端发来的 JSON Body 中读取用户信息！(100%不会丢)
        created_by = data.get('username') or data.get('created_by', '未知用户')
        created_role = data.get('userrole') or data.get('created_role', '未知角色')

        # 兼容兜底：如果前端没传，再去 Cookie 里找
        if created_by == '未知用户':
            created_by = request.COOKIES.get('username', '未知用户')
            created_role = request.COOKIES.get('userrole', '未知角色')
        
        # 解码，防止意外乱码
        created_by = unquote(created_by)
        created_role = unquote(created_role)
        
        if not remark_content:
            return Response({'error': '备注内容不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        
        new_remark = ProcurementRemark.objects.create(
            purchasing=purchasing_info,
            remark_content=remark_content,
            created_by=created_by,
            created_role=created_role
        )
        
        logger.info(f"成功添加备注，ID: {new_remark.id}, 创建人: {created_by}")
        return Response({
            'success': True, 
            'message': '备注添加成功', 
            'remark_id': new_remark.id,
            'created_by': created_by,
            'created_role': created_role
        })
        
    except ProcurementPurchasing.DoesNotExist:
        return Response({'error': '采购项目不存在'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': f'添加失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)