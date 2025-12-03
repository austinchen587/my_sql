from rest_framework.decorators import api_view
from rest_framework.response import Response
from ..serializers.daily_profit_stats import DailyProfitStatsSerializer
from ..services.daily_profit_service import DailyProfitService

@api_view(['GET'])
def daily_profit_stats(request):
    """获取每日利润统计数据"""
    try:
        # 调用服务层获取数据
        data = DailyProfitService.get_daily_profit_stats()
        
        # 使用序列化器返回标准化数据
        serializer = DailyProfitStatsSerializer(data, many=True)
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
