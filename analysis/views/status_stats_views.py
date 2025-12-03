from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from ..services.status_stats_service import StatusStatsService
from ..serializers.status_stats import ProcurementStatusStatsSerializer

@api_view(['GET'])
def procurement_status_stats(request):
    """
    获取采购项目按状态统计数据的API端点
    GET /api/analysis/status-stats/
    """
    try:
        # 从服务层获取数据
        stats_data = StatusStatsService.get_procurement_status_stats()
        
        # 验证和序列化数据
        serializer = ProcurementStatusStatsSerializer(data=stats_data, many=True)
        if serializer.is_valid():
            return Response({
                'success': True,
                'data': serializer.validated_data,
                'message': '状态统计数据获取成功'
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
            'error': f'获取状态统计数据时发生错误: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
