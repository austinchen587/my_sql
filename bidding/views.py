from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.db.models import Count
from .models import BiddingProject
from .serializers import BiddingHallSerializer

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