# emall_react/views.py
from rest_framework import generics, filters
from django_filters.rest_framework import DjangoFilterBackend
from emall.models import ProcurementEmall
from .serializers import EmallListSerializer
from .filters import ProcurementEmallFilter
from .pagination import EmallPagination
from .utils import get_numeric_price_for_item, check_price_condition

class EmallListView(generics.ListAPIView):
    """
    为React前端提供采购项目列表的API视图
    支持筛选功能：项目标题、采购单位、项目编号、控制总价、价格条件筛选、只看选择项目
    """
    queryset = ProcurementEmall.objects.all().order_by('-publish_date', '-id')
    serializer_class = EmallListSerializer
    pagination_class = EmallPagination
    
    # 配置过滤后端
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # 使用自定义过滤器
    filterset_class = ProcurementEmallFilter
    
    # 搜索字段（全局搜索）
    search_fields = ['project_title', 'purchasing_unit', 'project_number', 'total_price_control']
    
    # 排序字段
    ordering_fields = ['publish_date', 'quote_end_time']
    ordering = ['-publish_date']  # 默认按发布时间倒序

    def get_queryset(self):
        """
        添加价格条件筛选逻辑
        """
        queryset = super().get_queryset()
        
        # 获取价格条件参数
        price_condition = self.request.query_params.get('total_price_condition')
        
        if price_condition:
            # 使用Python进行内存筛选（适用于数据量不大的情况）
            filtered_items = []
            for item in queryset:
                numeric_price = get_numeric_price_for_item(item)
                if numeric_price is not None and check_price_condition(numeric_price, price_condition):
                    filtered_items.append(item.id)
            
            # 返回筛选后的查询集
            queryset = queryset.filter(id__in=filtered_items)
        
        # 示例：区域筛选
        region = self.request.query_params.get('region')
        if region:
            queryset = queryset.filter(region__icontains=region)
            
        return queryset

    def list(self, request, *args, **kwargs):
        """重写list方法添加调试"""
        print("🚀 emall_react视图被调用!")
        print(f"📋 请求参数: {dict(request.query_params)}")
        response = super().list(request, *args, **kwargs)
        print(f"📦 响应数据包含 {len(response.data.get('results', []))} 个项目")
        return response
