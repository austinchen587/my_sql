# emall_purchasing/views/select_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import ProcurementPurchasing
from emall.models import ProcurementEmall
from ..serializers import ProcurementPurchasingSerializer
from .username_utils import get_username_from_request  # 新增导入
import logging

logger = logging.getLogger(__name__)

class ProcurementSelectView(APIView):
    """采购选择视图 - 修复版本"""
    def post(self, request, procurement_id):
        try:
            procurement = ProcurementEmall.objects.get(id=procurement_id)
            
            # 从请求中获取当前用户名
            current_user = get_username_from_request(request)
            logger.info(f"选择项目操作，当前用户: {current_user}, 项目ID: {procurement_id}")
            
            # 创建或更新采购记录
            purchasing_info, created = ProcurementPurchasing.objects.get_or_create(
                procurement=procurement,
                defaults={
                    'is_selected': True,
                    'project_owner': current_user  # 创建时设置项目归属人
                }
            )
            
            if not created:
                # 如果是取消选择，清空项目归属人；如果是选择，设置项目归属人
                if purchasing_info.is_selected:
                    # 取消选择
                    purchasing_info.is_selected = False
                    purchasing_info.project_owner = '未分配'  # 取消选择时重置归属人
                else:
                    # 选择项目
                    purchasing_info.is_selected = True
                    purchasing_info.project_owner = current_user  # 设置当前用户为归属人
                
                purchasing_info.save()
            
            logger.info(f"项目选择状态更新成功: {purchasing_info.is_selected}, 归属人: {purchasing_info.project_owner}")
            
            return Response({
                'success': True,
                'is_selected': purchasing_info.is_selected,
                'project_owner': purchasing_info.project_owner,
                'message': '选择状态更新成功'
            })
            
        except ProcurementEmall.DoesNotExist:
            logger.error(f"采购项目不存在，ID: {procurement_id}")
            return Response({
                'success': False, 
                'error': '采购项目不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"选择项目失败，错误: {str(e)}")
            return Response({
                'success': False, 
                'error': f'操作失败: {str(e)}'
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProcurementPurchasingListView(APIView):
    """已选择的采购项目列表"""
    def get(self, request):
        purchasing_list = ProcurementPurchasing.objects.filter(is_selected=True)
        serializer = ProcurementPurchasingSerializer(purchasing_list, many=True)
        return Response(serializer.data)
