from rest_framework import generics, filters
from django_filters.rest_framework import DjangoFilterBackend
from emall.models import ProcurementEmall
from .serializers import EmallListSerializer

class EmallListView(generics.ListAPIView):
    """
    为React前端提供采购项目列表的API视图
    继承自ListAPIView，自动提供GET方法返回对象列表
    """
    # 1. 指定查询集（从主emall app导入模型）
    # 按发布时间倒序排列，最新的在前面
    queryset = ProcurementEmall.objects.all().order_by('-publish_date', '-id')
    
    # 2. 指定使用的序列化器
    serializer_class = EmallListSerializer
    
    # 3. (可选) 配置过滤后端，为后续添加搜索过滤功能做准备
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # 3.1 (可选) 定义可搜索的字段
    search_fields = ['project_title', 'purchasing_unit', 'project_name', 'region']
    
    # 3.2 (可选) 定义精确过滤的字段
    # filterset_fields = ['region', 'purchasing_unit'] # 需要先定义filterset_class或使用DjangoFilterBackend的默认行为
    
    # 3.3 (可选) 定义排序字段
    ordering_fields = ['publish_date', 'quote_end_time', 'total_price_control']
    ordering = ['-publish_date']  # 默认排序

    # 4. (可选) 如果需要自定义分页，可以在这里设置
    # pagination_class = YourCustomPaginationClass

    # 5. (可选) 如果需要重写获取查询集的逻辑，可以添加以下方法
    # def get_queryset(self):
    #     """
    #     可以在这里添加更复杂的查询逻辑，比如基于用户权限过滤数据
    #     """
    #     queryset = super().get_queryset()
    #     # 示例：只返回特定区域的数据
    #     # region = self.request.query_params.get('region', None)
    #     # if region is not None:
    #     #     queryset = queryset.filter(region=region)
    #     return queryset

    # 6. (可选) 如果需要自定义API响应格式，可以重写list方法
    # def list(self, request, *args, **kwargs):
    #     response = super().list(request, args, kwargs)
    #     # 可以在这里自定义返回的数据结构
    #     # 例如： response.data = {'code': 200, 'message': 'success', 'data': response.data}
    #     return response
