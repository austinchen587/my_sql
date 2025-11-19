from django.db.models import Q
from django.views.generic import TemplateView
from django_filters import rest_framework as filters
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from .models import ProcurementEmall
from .serializers import ProcurementEmallSerializer
import logging

logger = logging.getLogger(__name__)

class ProcurementListView(TemplateView):
    template_name = 'emall/procurement_list.html'

class DataTablesPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'length'
    max_page_size = 500

    def get_paginated_response(self, data):
        return Response({
            "draw": int(self.request.query_params.get('draw', 1)),
            "recordsTotal": self.page.paginator.count,
            "recordsFiltered": self.page.paginator.count,
            "data": data
        })

class ProcurementEmallFilter(filters.FilterSet):
    project_title = filters.CharFilter(lookup_expr='icontains')
    purchasing_unit = filters.CharFilter(lookup_expr='icontains')
    total_price_control = filters.CharFilter(lookup_expr='icontains')
    region = filters.CharFilter(lookup_expr='icontains')
    
    class Meta:
        model = ProcurementEmall
        fields = ['project_title', 'purchasing_unit', 'total_price_control', 'region']

class ProcurementListDataView(ListAPIView):
    serializer_class = ProcurementEmallSerializer
    pagination_class = DataTablesPagination
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = ProcurementEmallFilter

    def get_queryset(self):
        queryset = ProcurementEmall.objects.all()  # 移除了 select_related('category')
        
        # 搜索处理
        search_value = self.request.query_params.get('search[value]', '')
        if search_value:
            queryset = queryset.filter(
                Q(project_title__icontains=search_value) |
                Q(purchasing_unit__icontains=search_value) |
                Q(project_number__icontains=search_value) |
                Q(region__icontains=search_value)
            )
        
        # 排序处理
        ordering_column = self.request.query_params.get('order[0][column]')
        if ordering_column:
            ordering_field = self.request.query_params.get(f'columns[{ordering_column}][data]')
            ordering_dir = self.request.query_params.get('order[0][dir]', 'asc')
            if ordering_field:
                order_by = f'-{ordering_field}' if ordering_dir == 'desc' else ordering_field
                queryset = queryset.order_by(order_by)
        
        return queryset

class ProcurementDetailView(RetrieveAPIView):
    queryset = ProcurementEmall.objects.all()
    serializer_class = ProcurementEmallSerializer
    lookup_field = 'pk'
