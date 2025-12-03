from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from ..services.dashboard_service import DashboardService
from ..serializers.dashboard import DashboardStatsSerializer

@api_view(['GET'])
def procurement_dashboard_stats(request):
    """
    获取采购项目仪表盘统计数据的API端点
    GET /api/analysis/dashboard-stats/
    """
    try:
        # 从服务层获取数据
        stats_data = DashboardService.get_procurement_dashboard_stats()
        
        # 验证和序列化数据
        serializer = DashboardStatsSerializer(data=stats_data)
        if serializer.is_valid():
            return Response({
                'success': True,
                'data': serializer.validated_data,
                'message': '统计数据获取成功'
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
            'error': f'获取统计数据时发生错误: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
