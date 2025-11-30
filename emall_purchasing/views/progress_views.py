# emall_purchasing/views/progress_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
import logging
import traceback
from django.conf import settings

from .progress_services import ProcurementProgressService
from ..models import ProcurementPurchasing

logger = logging.getLogger(__name__)

class ProcurementProgressView(APIView):
    """采购进度管理视图"""
    
    def get(self, request, procurement_id):
        """获取采购进度信息"""
        try:
            logger.info(f"开始获取采购进度信息，ID: {procurement_id}")
            
            service = ProcurementProgressService()
            response_data = service.get_procurement_progress(procurement_id)
            
            logger.info(f"成功构建响应数据，供应商数量: {len(response_data['suppliers_info'])}, 备注数量: {len(response_data['remarks_history'])}")
            return Response(response_data)
            
        except ProcurementPurchasing.DoesNotExist:
            logger.error(f"采购进度信息不存在，ID: {procurement_id}")
            return Response({
                'error': '采购进度信息不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"获取数据失败，ID: {procurement_id}, 错误: {str(e)}", exc_info=True)
            return Response({
                'error': f'获取数据失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def update_purchasing_info(request, procurement_id):
    """更新采购进度信息"""
    try:
        logger.info(f"开始更新采购进度信息，ID: {procurement_id}")
        
        service = ProcurementProgressService()
        result = service.update_procurement_info(procurement_id, request)
        
        logger.info(f"成功更新采购进度信息，ID: {procurement_id}")
        return Response(result)
        
    except ProcurementPurchasing.DoesNotExist:
        logger.error(f"采购项目不存在，ID: {procurement_id}")
        return Response({'error': '采购项目不存在'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"更新采购进度信息失败，ID: {procurement_id}, 错误: {str(e)}")
        logger.error(traceback.format_exc())
        return Response({
            'error': f'更新失败: {str(e)}',
            'details': traceback.format_exc() if settings.DEBUG else None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _log_user_info(self, request):
    """记录用户信息用于调试"""
    logger.info(f"请求cookies: {dict(request.COOKIES)}")
    logger.info(f"session数据: {dict(request.session)}")
    
    # 添加请求头信息调试
    encoded_username = request.META.get('HTTP_X_USERNAME')
    if encoded_username:
        from .progress_handlers import decode_username_from_header
        decoded_username = decode_username_from_header(encoded_username)
        logger.info(f"请求头中的用户名 - 编码: {encoded_username}, 解码: {decoded_username}")
    
    if hasattr(request, 'user'):
        logger.info(f"用户对象: {request.user} (认证: {request.user.is_authenticated})")
        if request.user.is_authenticated:
            logger.info(f"认证用户: {request.user.username} ({request.user.id})")