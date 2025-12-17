# fp_emall/views/fp_emall_list_views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from ..services.fp_emall_list_service import FpEmallListService
from ..serializers.fp_emall_list_serializer import FpEmallSerializer  # 修改这里

@api_view(['GET'])
def fp_emall_list(request):
    """获取FP Emall列表"""
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 100))
        
        # 调用服务层获取数据
        data = FpEmallListService.get_fp_emall_list(page, page_size)
        total_count = FpEmallListService.get_total_count()
        
        # 使用序列化器 - 类名改为 FpEmallSerializer
        serializer = FpEmallSerializer(data, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': (total_count + page_size - 1) // page_size
            }
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)
