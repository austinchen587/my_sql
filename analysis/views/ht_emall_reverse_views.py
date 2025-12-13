from rest_framework.decorators import api_view
from rest_framework.response import Response
from ..serializers.ht_emall_reverse import HtEmallReverseRecordSerializer
from ..services.ht_emall_reverse import HtEmallReverseService

@api_view(['GET'])
def ht_emall_reverse_records(request):
    """
    获取 HT 电商平台反拍项目全部记录
    """
    try:
        data = HtEmallReverseService.get_ht_emall_reverse_records()
        serializer = HtEmallReverseRecordSerializer(data, many=True)
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
