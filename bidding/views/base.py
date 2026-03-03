# bidding/views/base.py
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, OuterRef, Subquery, CharField, DateTimeField
from django.db.models.functions import Coalesce  # [新增] 用于合并双表查询
from ..models import BiddingProject
from ..serializers import BiddingHallSerializer
from emall_purchasing.models import UnifiedProcurementRemark, ProcurementRemark  # [新增] 引入两张备注表
import logging

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 16
    page_size_query_param = 'page_size'
    max_page_size = 100

class BiddingProjectListView(generics.ListAPIView):
    """
    大厅列表接口 - 包含最新备注预查询 (双表合并查询 + 外键直连终极兼容版)
    """
    serializer_class = BiddingHallSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        qs = BiddingProject.objects.select_related(
            'source_emall', 
            'source_emall__purchasing_info'
        ).all()
        
        # [极度稳定版修复]：直接使用当前表的原生外键 source_emall_id 进行关联
        # 彻底抛弃 OuterRef 里的跨表双下划线，避免不同数据库的解析兼容性问题
        
        # 1. 查询未认领时的统一备注表
        unified_remarks = UnifiedProcurementRemark.objects.filter(
            procurement_id=OuterRef('source_emall_id')
        ).order_by('-created_at')

        # 2. 查询已认领后的采购专属备注表
        # 通过采购表逆向查回 procurement_id，与主表的 source_emall_id 匹配
        purchasing_remarks = ProcurementRemark.objects.filter(
            purchasing__procurement_id=OuterRef('source_emall_id')
        ).order_by('-created_at')

        # 3. 使用 Coalesce 合并。优先拿专属表(较新)，如果专属表没有，再拿统一表
        qs = qs.annotate(
            latest_remark_content=Coalesce(
                Subquery(purchasing_remarks.values('remark_content')[:1], output_field=CharField()),
                Subquery(unified_remarks.values('remark_content')[:1], output_field=CharField())
            ),
            latest_remark_by=Coalesce(
                Subquery(purchasing_remarks.values('created_by')[:1], output_field=CharField()),
                Subquery(unified_remarks.values('created_by')[:1], output_field=CharField())
            ),
            latest_remark_at=Coalesce(
                Subquery(purchasing_remarks.values('created_at')[:1], output_field=DateTimeField()),
                Subquery(unified_remarks.values('created_at')[:1], output_field=DateTimeField())
            )
        )
        
        p = self.request.query_params
        
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

        owner = p.get('owner')
        if owner:
            qs = qs.filter(source_emall__purchasing_info__project_owner__icontains=owner)

        is_selected = p.get('is_selected')
        if is_selected:
            if str(is_selected).lower() == 'true':
                qs = qs.filter(source_emall__purchasing_info__is_selected=True)
            elif str(is_selected).lower() == 'false':
                qs = qs.filter(
                    Q(source_emall__purchasing_info__is_selected=False) | 
                    Q(source_emall__purchasing_info__isnull=True)
                )
        
        # 按照主键倒序排列，保证最新抓取的数据在最前
        return qs.order_by('-pk')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['view_type'] = 'list'
        return context

class BiddingProjectDetailView(generics.RetrieveAPIView):
    queryset = BiddingProject.objects.select_related('source_emall').all()
    serializer_class = BiddingHallSerializer
    lookup_field = 'pk'
    lookup_url_kwarg = 'id'