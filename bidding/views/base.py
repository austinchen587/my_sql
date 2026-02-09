# bidding/views/base.py
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from ..models import BiddingProject
from ..serializers import BiddingHallSerializer
import sys

# 自定义分页器
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 16
    page_size_query_param = 'page_size'
    max_page_size = 100

class BiddingProjectListView(generics.ListAPIView):
    """
    大厅列表接口 - 修复归属人和状态筛选
    """
    serializer_class = BiddingHallSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        # 1. 强制打印日志，证明新代码被加载了
        print("\033[92m" + "="*50 + "\033[0m")
        print(f"\033[92m[Debug] 正在执行 BiddingProjectListView (base.py) \033[0m")
        
        qs = BiddingProject.objects.select_related(
            'source_emall', 
            'source_emall__purchasing_info'
        ).all()
        
        p = self.request.query_params
        print(f"\033[93m[Debug] 收到前端参数: {dict(p)}\033[0m")

        # 2. 关键词搜索
        search_term = p.get('search')
        if search_term:
            qs = qs.filter(title__icontains=search_term)
        
        # 3. 基础属性过滤
        if p.get('province'):
            qs = qs.filter(province=p.get('province'))
        if p.get('root'):
            qs = qs.filter(root_category=p.get('root'))
        
        # 只有在 root=goods 时才进行二级分类筛选
        if p.get('sub') and p.get('root') == 'goods':
            qs = qs.filter(sub_category=p.get('sub'))
            
        if p.get('mode'):
            qs = qs.filter(mode=p.get('mode'))

        # 4. [关键修复] 归属人搜索
        owner = p.get('owner')
        if owner:
            print(f"\033[96m[Debug] 正在过滤归属人: {owner}\033[0m")
            qs = qs.filter(source_emall__purchasing_info__project_owner__icontains=owner)

        # 5. [关键修复] 已选项目搜索
        is_selected = p.get('is_selected')
        if is_selected:
            print(f"\033[96m[Debug] 正在过滤状态: {is_selected}\033[0m")
            if str(is_selected).lower() == 'true':
                qs = qs.filter(source_emall__purchasing_info__is_selected=True)
            elif str(is_selected).lower() == 'false':
                # 未选中包括：记录存在且为False，或者记录根本不存在(isnull=True)
                qs = qs.filter(
                    Q(source_emall__purchasing_info__is_selected=False) | 
                    Q(source_emall__purchasing_info__isnull=True)
                )
        
        count = qs.count()
        print(f"\033[92m[Debug] 最终返回数据量: {count}\033[0m")
        print("\033[92m" + "="*50 + "\033[0m")
        
        # 排序：状态优先，时间次之
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