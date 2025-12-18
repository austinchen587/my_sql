# analysis/views/monthly_profit_views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from ..serializers.monthly_profit_summary import MonthlyProfitSummarySerializer
from ..services.monthly_profit_service import MonthlyProfitService

@api_view(['GET'])
def monthly_profit_summary(request):
    """获取月度利润汇总数据"""
    try:
        data = MonthlyProfitService.get_monthly_profit_summary()
        serializer = MonthlyProfitSummarySerializer(data, many=True)
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
