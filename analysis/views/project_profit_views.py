# analysis/views/project_profit_views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from ..serializers.project_profit_stats import ProjectProfitStatsSerializer
from ..services.project_profit_service import ProjectProfitService

@api_view(['GET'])
def project_profit_stats(request):
    """获取项目利润统计数据"""
    try:
        data = ProjectProfitService.get_project_profit_stats()
        serializer = ProjectProfitStatsSerializer(data, many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'count': len(data)
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)
