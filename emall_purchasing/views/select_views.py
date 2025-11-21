from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import ProcurementPurchasing
from emall.models import ProcurementEmall
from ..serializers import ProcurementPurchasingSerializer

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

class ProcurementPurchasingListView(APIView):
    """已选择的采购项目列表"""
    def get(self, request):
        purchasing_list = ProcurementPurchasing.objects.filter(is_selected=True)
        serializer = ProcurementPurchasingSerializer(purchasing_list, many=True)
        return Response(serializer.data)
