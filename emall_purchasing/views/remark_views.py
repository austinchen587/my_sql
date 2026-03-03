# emall_purchasing/views/remark_views.py
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model  # [核心引入]
from ..models import ProcurementPurchasing, ProcurementRemark
from .utils import safe_json_loads
import logging
from urllib.parse import unquote

logger = logging.getLogger(__name__)
User = get_user_model()  # 获取当前系统的用户表

@api_view(['POST'])
@authentication_classes([]) # 保持禁用以跳过 CSRF 拦截
@permission_classes([AllowAny]) 
def add_remark(request, procurement_id):
    try:
        logger.info(f"开始添加备注，采购项目ID: {procurement_id}")
        purchasing_info = ProcurementPurchasing.objects.get(procurement_id=procurement_id)
        data = safe_json_loads(request)
        
        if not data:
            return Response({'error': '无效的JSON数据'}, status=status.HTTP_400_BAD_REQUEST)
        
        remark_content = data.get('remark_content', '').strip()
        
        created_by = '未知用户'
        created_role = '未知角色'

        # 🌟 终极修复：绕过 DRF 认证，直接从底层 Django Session 中提取用户！
        # 即使关闭了 Auth，Django 的 SessionMiddleware 依然会解析 sessionid Cookie
        django_request = getattr(request, '_request', request)
        
        if hasattr(django_request, 'session'):
            # '_auth_user_id' 是 Django 登录后写入 session 的标准内置 key
            user_id = django_request.session.get('_auth_user_id')
            if user_id:
                try:
                    # 拿到 ID 后直接查库，100% 准确，无视跨域与请求头限制
                    user_obj = User.objects.get(pk=user_id)
                    created_by = user_obj.username
                    if hasattr(user_obj, 'userprofile'):
                        created_role = user_obj.userprofile.role
                except User.DoesNotExist:
                    pass
        
        # 兜底：如果由于某种原因 Session 清空了，再尝试常规提取
        if created_by == '未知用户':
            created_by = data.get('username', request.COOKIES.get('username', '未知用户'))
            created_role = data.get('userrole', request.COOKIES.get('userrole', '未知角色'))
        
        # 解码，防止意外乱码 (比如前端存 Cookie 时是 %E5...)
        if created_by != '未知用户':
            created_by = unquote(created_by)
        if created_role != '未知角色':
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