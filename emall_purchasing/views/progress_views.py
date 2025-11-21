from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import ProcurementPurchasing, ProcurementRemark
from emall.models import ProcurementEmall
from ..serializers import ProcurementPurchasingSerializer

class ProcurementProgressView(APIView):
    """采购进度管理视图"""
    
    def get(self, request, procurement_id):
        """获取采购进度信息和备注历史"""
        try:
            purchasing_info = ProcurementPurchasing.objects.get(procurement_id=procurement_id)
            serializer = ProcurementPurchasingSerializer(purchasing_info)
            return Response(serializer.data)
        except ProcurementPurchasing.DoesNotExist:
            return Response({
                'error': '采购进度信息不存在'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def post(self, request, procurement_id):
        """更新采购进度信息和添加备注"""
        try:
            procurement = ProcurementEmall.objects.get(id=procurement_id)
            purchasing_info, created = ProcurementPurchasing.objects.get_or_create(
                procurement=procurement
            )
            
            # 处理新增备注
            new_remark = request.data.get('new_remark')
            if new_remark:
                ProcurementRemark.objects.create(
                    purchasing=purchasing_info,
                    remark_content=new_remark.get('content', ''),
                    created_by=new_remark.get('created_by', '系统')
                )
                # 更新主备注字段
                if 'remarks' in request.data:
                    request.data['remarks'] = purchasing_info.remarks + "\n" + new_remark.get('content', '') if purchasing_info.remarks else new_remark.get('content', '')
            
            serializer = ProcurementPurchasingSerializer(
                purchasing_info, 
                data=request.data, 
                partial=True
            )
            
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'success': True, 
                    'message': '采购进度更新成功',
                    'data': serializer.data
                })
                
            return Response({
                'success': False, 
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except ProcurementEmall.DoesNotExist:
            return Response({
                'success': False, 
                'error': '采购项目不存在'
            }, status=status.HTTP_404_NOT_FOUND)
