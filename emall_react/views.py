# emall_react/views.py
from rest_framework import generics, filters
from django_filters.rest_framework import DjangoFilterBackend
from emall.models import ProcurementEmall
from .serializers import EmallListSerializer
from .filters import ProcurementEmallFilter
from .pagination import EmallPagination
from .utils import get_numeric_price_for_item, check_price_condition
from django.db.models import Prefetch
from emall_purchasing.models import ProcurementPurchasing, ProcurementRemark  # 添加导入

class EmallListView(generics.ListAPIView):
    """
    为React前端提供采购项目列表的API视图
    支持筛选功能：项目标题、采购单位、项目编号、控制总价、价格条件筛选、只看选择项目
    """
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
        优化查询性能，预取相关数据
        """
        # 预取采购信息和备注
        queryset = ProcurementEmall.objects.prefetch_related(
            Prefetch(
                'purchasing_info',
                queryset=ProcurementPurchasing.objects.select_related('procurement')
            ),
            Prefetch(
                'purchasing_info__remarks_history',
                queryset=ProcurementRemark.objects.order_by('-created_at'),
                to_attr='prefetched_remarks'
            ),
            Prefetch(
                'purchasing_info__suppliers'
            )
        ).order_by('-publish_date', '-id')
        
        # 价格条件筛选逻辑
        price_condition = self.request.query_params.get('total_price_condition')
        
        if price_condition:
            # 使用Python进行内存筛选
            filtered_items = []
            for item in queryset:
                numeric_price = get_numeric_price_for_item(item)
                if numeric_price is not None and check_price_condition(numeric_price, price_condition):
                    filtered_items.append(item.id)
            
            # 返回筛选后的查询集
            queryset = queryset.filter(id__in=filtered_items)
        
        # 区域筛选
        region = self.request.query_params.get('region')
        if region:
            queryset = queryset.filter(region__icontains=region)
            
        # 只看选择项目筛选
        only_selected = self.request.query_params.get('only_selected')
        if only_selected and only_selected.lower() == 'true':
            queryset = queryset.filter(purchasing_info__is_selected=True)
        
        return queryset

    def list(self, request, *args, **kwargs):
        """重写list方法添加调试"""
        print("🚀 emall_react视图被调用!")
        print(f"📋 请求参数: {dict(request.query_params)}")
        response = super().list(request, *args, **kwargs)
        print(f"📦 响应数据包含 {len(response.data.get('results', []))} 个项目")
        
        # 调试输出第一个项目的数据结构
        if response.data.get('results'):
            first_item = response.data['results'][0]
            print(f"🔍 第一个项目数据结构: {list(first_item.keys())}")
            print(f"📝 第一个项目备注: {first_item.get('latest_remark')}")
            print(f"👤 第一个项目归属人: {first_item.get('project_owner')}")
            print(f"🏢 第一个项目供应商数量: {first_item.get('suppliers_count')}")
        
        return response
