# fp_emall/views/fp_emall_search_views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from ..services.fp_emall_search_service import FpEmallSearchService
from ..serializers.fp_emall_search_serializer import FpEmallSearchSerializer

@api_view(['GET'])
def fp_emall_search(request):
    """FP Emall 搜索接口"""
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 100))
        search = request.GET.get('search', '').strip()
        search_field = request.GET.get('search_field', '').strip()
        
        # 调试日志：打印接收到的参数
        print(f"VIEW DEBUG - search: '{search}', search_field: '{search_field}'")
        
        # 调用搜索服务获取数据
        data = FpEmallSearchService.search_fp_emall(
            page=page, 
            page_size=page_size,
            search=search,
            search_field=search_field
        )
        
        total_count = FpEmallSearchService.get_search_count(
            search=search,
            search_field=search_field
        )
        
        # 使用序列化器
        serializer = FpEmallSearchSerializer(data, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'pagination': {
                'page':page,
                'page_size': page_size,  # 修复这里：price_size -> page_size
                'total_count': total_count,
                'total_pages': (total_count + page_size - 1) // page_size  # 这里也要修复
            },
            'search_info': {
                'search_query': search,
                'search_field': search_field,
                'has_search': bool(search)
            }
        })
    except Exception as e:
        import traceback
        print(f"SEARCH ERROR: {str(e)}")
        print(traceback.format_exc())
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
def get_search_fields(request):
    """获取可搜索字段列表"""
    try:
        fields = FpEmallSearchService.get_search_fields()
        return Response({
            'success': True,
            'data': fields
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)
