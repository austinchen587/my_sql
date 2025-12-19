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
    """添加备注 - 自动从cookies获取用户信息"""
    try:
        logger.info(f"开始添加备注，采购项目ID: {procurement_id}")
        purchasing_info = ProcurementPurchasing.objects.get(procurement_id=procurement_id)
        data = safe_json_loads(request)
        
        if not data:
            return Response({'error': '无效的JSON数据'}, status=status.HTTP_400_BAD_REQUEST)
        
        remark_content = data.get('remark_content', '').strip()
        
        # 从cookies中获取用户信息
        created_by = request.COOKIES.get('username', '未知用户')
        created_role = request.COOKIES.get('userrole', '未知角色')  # 添加角色获取
        
        # 如果cookies中没有用户名，尝试从session或其他地方获取
        if created_by == '未知用户':
            if hasattr(request, 'user') and request.user.is_authenticated:
                created_by = request.user.username
                # 如果需要从用户对象获取角色
                if hasattr(request.user, 'role'):
                    created_role = request.user.role
            elif request.session.get('username'):
                created_by = request.session['username']
                created_role = request.session.get('userrole', '未知角色')
        
        if not remark_content:
            return Response({'error': '备注内容不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        
        new_remark = ProcurementRemark.objects.create(
            purchasing=purchasing_info,
            remark_content=remark_content,
            created_by=created_by,
            created_role=created_role  # 现在这个变量已经定义了
        )
        
        logger.info(f"成功添加备注，ID: {new_remark.id}, 创建人: {created_by}, 角色: {created_role}")
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
