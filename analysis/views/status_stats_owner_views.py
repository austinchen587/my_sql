from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from ..services.status_stats_owner_service import StatusStatsOwnerService
from ..serializers.status_stats_owner import ProcurementStatusStatsOwnerSerializer

@api_view(['GET'])
def procurement_status_stats_by_owner(request):
    """
    获取采购项目按归属人竞标状态统计数据的API端点
    GET /api/analysis/status-stats-owner/?owner=陈少帅
    """
    try:
        # 从查询参数获取归属人姓名
        owner_name = request.GET.get('owner', '')
        if not owner_name:
            return Response({
                'success': False,
                'error': '请提供归属人参数'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 从服务层获取数据
        stats_data = StatusStatsOwnerService.get_procurement_status_stats_by_owner(owner_name)
        
        # 验证和序列化数据
        serializer = ProcurementStatusStatsOwnerSerializer(data=stats_data, many=True)
        if serializer.is_valid():
            return Response({
                'success': True,
                'data': serializer.validated_data,
                'message': f'{owner_name}的竞标状态统计数据获取成功',
                'owner': owner_name
            })
        else:
            return Response({
                'success': False,
                'error': '数据序列化失败',
                'details': serializer.errors
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        return Response({
            'success': False,
            'error': f'获取归属人竞标状态统计数据时发生错误: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
