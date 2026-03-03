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
@authentication_classes([]) # 禁用DRF默认认证，跳过CSRF检查
@permission_classes([AllowAny]) # 允许所有访问
def add_remark(request, procurement_id):
    """添加备注 - 全方位获取用户信息版"""
    try:
        logger.info(f"开始添加备注，采购项目ID: {procurement_id}")
        purchasing_info = ProcurementPurchasing.objects.get(procurement_id=procurement_id)
        data = safe_json_loads(request)
        
        if not data:
            return Response({'error': '无效的JSON数据'}, status=status.HTTP_400_BAD_REQUEST)
        
        remark_content = data.get('remark_content', '').strip()
        
        # --- 用户身份获取逻辑 (全能增强版) ---
        created_by = '未知用户'
        created_role = '未知角色'

        # 1. 优先尝试从 Django 原生 Request 获取 (应对 Session Auth)
        django_user = getattr(request._request, 'user', None)
        if django_user and django_user.is_authenticated:
            created_by = django_user.username
            try:
                created_role = django_user.userprofile.role
            except:
                pass
        
        # 2. 尝试从 Session 字典获取
        if created_by == '未知用户' and request.session.get('username'):
            created_by = request.session['username']
            created_role = request.session.get('userrole', '未知角色')
            
        # 3. [新增核心] 尝试从 Headers 请求头获取 (应对前端放进 Header 的情况)
        if created_by == '未知用户':
            # 兼容常见的几种自定义 Header 命名
            created_by = request.headers.get('X-User-Name') or request.headers.get('Username', '未知用户')
            created_role = request.headers.get('X-User-Role') or request.headers.get('Userrole', '未知角色')
        
        # 4. 最后尝试从 Cookies 获取
        if created_by == '未知用户':
            created_by = request.COOKIES.get('username', '未知用户')
            created_role = request.COOKIES.get('userrole', '未知角色')
        
        # [核心修复]：统一对最终获取到的信息进行 URL 解码！
        # 即使前端传了 %E5%B0%8F%E5%85%9C，在这里也会被完美还原成 "小兜"
        if created_by and created_by != '未知用户':
            created_by = unquote(created_by)
        if created_role and created_role != '未知角色':
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
        logger.error(f"采购项目不存在，ID: {procurement_id}")
        return Response({'error': '采购项目不存在'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"添加备注失败，错误: {str(e)}", exc_info=True)
        return Response({'error': f'添加失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)