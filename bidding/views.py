from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.db.models import Count
from .models import BiddingProject
from .serializers import BiddingHallSerializer

from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response

from rest_framework.views import APIView  # 引入 APIView

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 16
    page_size_query_param = 'page_size'
    max_page_size = 100

class BiddingProjectListView(generics.ListAPIView):
    """大厅列表接口"""
    serializer_class = BiddingHallSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        qs = BiddingProject.objects.select_related('source_emall').all()
        p = self.request.query_params

        search_term = p.get('search')
        if search_term:
            qs = qs.filter(title__icontains=search_term)
        
        if p.get('province'): qs = qs.filter(province=p.get('province'))
        if p.get('root'): qs = qs.filter(root_category=p.get('root'))
        if p.get('sub') and p.get('root') == 'goods': qs = qs.filter(sub_category=p.get('sub'))
        if p.get('mode'): qs = qs.filter(mode=p.get('mode'))
        
        return qs.order_by('status', 'start_time')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['view_type'] = 'list'
        return context
    

class ProvinceStatsView(generics.GenericAPIView):
    """门户接口：返回各省份的项目数量"""
    def get(self, request):
        # [核心修复] 必须用 'pk' 统计，因为模型里已经没有 'id' 字段了
        data = BiddingProject.objects.values('province').annotate(count=Count('pk'))
        result = {item['province']: item['count'] for item in data}
        return Response(result)

class BiddingProjectDetailView(generics.RetrieveAPIView):
    """详情接口"""
    queryset = BiddingProject.objects.select_related('source_emall').all()
    serializer_class = BiddingHallSerializer
    
    # [核心修复] 
    # lookup_field = 'pk'   -> 告诉 Django 查库时用主键 (pk) 查
    # lookup_url_kwarg = 'id' -> 告诉 Django URL 里的参数名叫 'id' (<int:id>)
    lookup_field = 'pk'
    lookup_url_kwarg = 'id'


class BiddingStatsView(APIView):
    """
    独立出来的统计接口 - v2.2 (含子类目归属人详情)
    URL: /api/bidding/project/stats/?province=JX
    """
    def get(self, request):
        now = timezone.now()
        province = request.query_params.get('province')
        
        # 1. 基础过滤：未过期 + 物资类 (goods)
        qs = BiddingProject.objects.filter(end_time__gt=now, root_category='goods')
        
        # 2. 分省过滤
        if province:
            qs = qs.filter(province=province)

        # === 统计 1：物资子类目分布 (7个分类) ===
        # 获取所有定义的子类目字典
        sub_cats_def = dict(BiddingProject.SUB_CATS) 
        
        # A. 基础统计：总数、已选数
        sub_stats = qs.values('sub_category').annotate(
            total=Count('pk'),
            selected=Count('pk', filter=Q(source_emall__purchasing_info__is_selected=True))
        )
        sub_lookup = {item['sub_category']: item for item in sub_stats}

        # B. [核心新增] 归属人详情统计：按 子类目 + 归属人 分组
        # SQL 类似: GROUP BY sub_category, project_owner
        owner_stats = qs.filter(source_emall__purchasing_info__is_selected=True).values(
            'sub_category', 
            'source_emall__purchasing_info__project_owner'
        ).annotate(count=Count('pk'))

        # 将归属人数据整理到字典中： { 'office': [{'name': '张三', 'count': 2}, ...], ... }
        category_owners_map = {}
        for item in owner_stats:
            cat = item['sub_category']
            owner = item['source_emall__purchasing_info__project_owner']
            count = item['count']
            
            if not owner: continue # 跳过未分配的
            
            if cat not in category_owners_map:
                category_owners_map[cat] = []
            category_owners_map[cat].append({'name': owner, 'count': count})

        # C. 组装最终的子类目列表
        sub_cats_data = []
        for key, label in sub_cats_def.items():
            stat = sub_lookup.get(key, {'total': 0, 'selected': 0})
            
            # 获取该类目下的归属人列表，并按数量倒序排列
            owners = category_owners_map.get(key, [])
            owners.sort(key=lambda x: x['count'], reverse=True)

            sub_cats_data.append({
                'key': key,
                'label': label,
                'total': stat['total'],
                'selected': stat['selected'],
                'unselected': stat['total'] - stat['selected'],
                'owners': owners  # <--- 将归属人详情放进对应的分类里
            })

        # === 统计 2：已选项目的总状态分布 (右侧卡片用) ===
        selected_qs = qs.filter(source_emall__purchasing_info__is_selected=True)
        status_data = selected_qs.values('source_emall__purchasing_info__bidding_status').annotate(
            count=Count('pk')
        )
        status_map = {}
        for item in status_data:
            key = item.get('source_emall__purchasing_info__bidding_status') or 'unknown'
            status_map[key] = item['count']

        # === 统计 3：总归属人榜单 (如果还需要总榜的话可以保留，不需要也可以删掉) ===
        owner_data = selected_qs.values('source_emall__purchasing_info__project_owner').annotate(
            count=Count('pk')
        ).order_by('-count')
        owners_list = []
        for item in owner_data:
            name = item.get('source_emall__purchasing_info__project_owner')
            if name: owners_list.append({'name': name, 'count': item['count']})

        return Response({
            "sub_cats": sub_cats_data,
            "status_dist": status_map,
            "owner_dist": owners_list
        })