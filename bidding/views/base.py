# bidding/views/base.py
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, OuterRef, Subquery, CharField, DateTimeField
from ..models import BiddingProject
from ..serializers import BiddingHallSerializer
# [新增] 引入备注模型
from emall_purchasing.models import UnifiedProcurementRemark
import logging
# 自定义分页器
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 16
    page_size_query_param = 'page_size'
    max_page_size = 100

class BiddingProjectListView(generics.ListAPIView):
    """
    大厅列表接口 - 包含最新备注预查询
    """
    serializer_class = BiddingHallSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        qs = BiddingProject.objects.select_related(
            'source_emall', 
            'source_emall__purchasing_info'
        ).all()
        
        # [核心修改] 预查询最新备注信息
        # 关联条件：UnifiedProcurementRemark.procurement == BiddingProject.source_emall
        newest_remarks = UnifiedProcurementRemark.objects.filter(
            procurement=OuterRef('source_emall')
        ).order_by('-created_at')

        # 使用 annotate 将子查询结果注入到每个对象中
        qs = qs.annotate(
            latest_remark_content=Subquery(newest_remarks.values('remark_content')[:1], output_field=CharField()),
            latest_remark_by=Subquery(newest_remarks.values('created_by')[:1], output_field=CharField()),
            latest_remark_at=Subquery(newest_remarks.values('created_at')[:1], output_field=DateTimeField())
        )
        
        p = self.request.query_params
        
        # ... (原有的过滤逻辑保持不变) ...
        search_term = p.get('search')
        if search_term:
            qs = qs.filter(title__icontains=search_term)
        
        if p.get('province'):
            qs = qs.filter(province=p.get('province'))
        if p.get('root'):
            qs = qs.filter(root_category=p.get('root'))
        if p.get('sub') and p.get('root') == 'goods':
            qs = qs.filter(sub_category=p.get('sub'))
        if p.get('mode'):
            qs = qs.filter(mode=p.get('mode'))

        # 归属人搜索
        owner = p.get('owner')
        if owner:
            qs = qs.filter(source_emall__purchasing_info__project_owner__icontains=owner)

        # 已选项目搜索
        is_selected = p.get('is_selected')
        if is_selected:
            if str(is_selected).lower() == 'true':
                qs = qs.filter(source_emall__purchasing_info__is_selected=True)
            elif str(is_selected).lower() == 'false':
                qs = qs.filter(
                    Q(source_emall__purchasing_info__is_selected=False) | 
                    Q(source_emall__purchasing_info__isnull=True)
                )
        
        return qs.order_by('status', 'start_time')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['view_type'] = 'list'
        return context

class BiddingProjectDetailView(generics.RetrieveAPIView):
    queryset = BiddingProject.objects.select_related('source_emall').all()
    serializer_class = BiddingHallSerializer
    lookup_field = 'pk'
    lookup_url_kwarg = 'id'