# emall_purchasing/views/remark_views.py
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from ..models import ProcurementPurchasing, ProcurementRemark
from .utils import safe_json_loads
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@authentication_classes([]) # [修复] 禁用DRF默认认证，从而跳过CSRF检查
@permission_classes([AllowAny]) # [修复] 允许所有访问
def add_remark(request, procurement_id):
    """添加备注 - 自动从cookies获取用户信息 (已修复CSRF问题)"""
    try:
        logger.info(f"开始添加备注，采购项目ID: {procurement_id}")
        purchasing_info = ProcurementPurchasing.objects.get(procurement_id=procurement_id)
        data = safe_json_loads(request)
        
        if not data:
            return Response({'error': '无效的JSON数据'}, status=status.HTTP_400_BAD_REQUEST)
        
        remark_content = data.get('remark_content', '').strip()
        
        # --- 用户身份获取逻辑 (增强版) ---
        created_by = '未知用户'
        created_role = '未知角色'

        # 1. 优先尝试从 Django 原生 Session 获取
        django_user = getattr(request._request, 'user', None)
        if django_user and django_user.is_authenticated:
            created_by = django_user.username
            try:
                created_role = django_user.userprofile.role
            except:
                pass
        
        # 2. 尝试从 Session 字典获取
        if created_by == '未知用户':
            if request.session.get('username'):
                created_by = request.session['username']
                created_role = request.session.get('userrole', '未知角色')
        
        # 3. 最后尝试从 Cookies 获取
        if created_by == '未知用户':
            created_by = request.COOKIES.get('username', '未知用户')
            created_role = request.COOKIES.get('userrole', '未知角色')
        
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
        logger.error(f"采购项目不存在，ID: {procurement_id}")
        return Response({'error': '采购项目不存在'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"添加备注失败，错误: {str(e)}", exc_info=True)
        return Response({'error': f'添加失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)