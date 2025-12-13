from rest_framework.decorators import api_view
from rest_framework.response import Response
from ..serializers.ht_emall import HtEmallRecordSerializer
from ..services.ht_emall_service import HtEmallService

@api_view(['GET'])
def ht_emall_records(request):
    """
    获取 HT 电商平台竞价项目全部记录
    """
    try:
        data = HtEmallService.get_ht_emall_records()
        serializer = HtEmallRecordSerializer(data, many=True)
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


