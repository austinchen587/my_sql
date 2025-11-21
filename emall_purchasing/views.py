from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ProcurementPurchasing
from emall.models import ProcurementEmall
from .serializers import ProcurementPurchasingSerializer

class ProcurementSelectView(APIView):
    """采购选择视图"""
    def post(self, request, procurement_id):
        try:
            procurement = ProcurementEmall.objects.get(id=procurement_id)
            
            # 创建或更新采购记录
            purchasing_info, created = ProcurementPurchasing.objects.get_or_create(
                procurement=procurement,
                defaults={'is_selected': True}
            )
            
            if not created:
                purchasing_info.is_selected = not purchasing_info.is_selected
                purchasing_info.save()
            
            return Response({
                'success': True,
                'is_selected': purchasing_info.is_selected,
                'message': '选择状态更新成功'
            })
            
        except ProcurementEmall.DoesNotExist:
            return Response({
                'success': False, 
                'error': '采购项目不存在'
            }, status=status.HTTP_404_NOT_FOUND)

class ProcurementProgressView(APIView):
    """采购进度管理视图"""
    
    def get(self, request, procurement_id):
        """获取采购进度信息"""
        try:
            purchasing_info = ProcurementPurchasing.objects.get(procurement_id=procurement_id)
            serializer = ProcurementPurchasingSerializer(purchasing_info)
            return Response(serializer.data)
        except ProcurementPurchasing.DoesNotExist:
            return Response({
                'error': '采购进度信息不存在'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def post(self, request, procurement_id):
        """更新采购进度信息"""
        try:
            procurement = ProcurementEmall.objects.get(id=procurement_id)
            purchasing_info, created = ProcurementPurchasing.objects.get_or_create(
                procurement=procurement
            )
            
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

class ProcurementPurchasingListView(APIView):
    """已选择的采购项目列表"""
    def get(self, request):
        purchasing_list = ProcurementPurchasing.objects.filter(is_selected=True)
        serializer = ProcurementPurchasingSerializer(purchasing_list, many=True)
        return Response(serializer.data)
