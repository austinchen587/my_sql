from django.db.models import Q
from django.views.generic import TemplateView
from django_filters import rest_framework as filters
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.core.paginator import InvalidPage
from rest_framework.exceptions import NotFound
from .models import ProcurementEmall
from .serializers import ProcurementEmallSerializer
import logging
import json
import re

logger = logging.getLogger(__name__)

class ProcurementListView(TemplateView):
    template_name = 'emall/procurement_list.html'

class DataTablesPagination(PageNumberPagination):
    page_size = 25  # 与前端 pageLength 保持一致
    page_size_query_param = 'length'
    max_page_size = 500

    def get_paginated_response(self, data):
        return Response({
            "draw": int(self.request.query_params.get('draw', 1)),
            "recordsTotal": self.page.paginator.count,
            "recordsFiltered": self.page.paginator.count,
            "data": data
        })

    def paginate_queryset(self, queryset, request, view=None):
        # 手动处理 DataTables 的分页参数
        page_size = self.get_page_size(request)
        if not page_size:
            return None

        paginator = self.django_paginator_class(queryset, page_size)
        
        # DataTables 使用 start 参数，我们需要将其转换为页码
        start = request.query_params.get('start', 0)
        try:
            start = int(start)
            # 计算页码：start / page_size + 1
            page_number = (start // page_size) + 1
        except (TypeError, ValueError):
            page_number = 1

        try:
            self.page = paginator.page(page_number)
        except InvalidPage as exc:
            msg = self.invalid_page_message.format(
                page_number=page_number, message=str(exc)
            )
            raise NotFound(msg)

        if paginator.num_pages > 1 and self.template is not None:
            self.display_page_controls = True

        self.request = request
        return list(self.page)

# 自定义金额转换函数（与前端保持一致，修正版）
# 自定义金额转换函数（与前端保持一致，修正版）
def convert_price_to_number(price_str):
    if not price_str:
        return None
    
    try:
        # 移除空格和逗号
        clean_str = str(price_str).replace(' ', '').replace(',', '')
        
        # 1. 先检查"万元"（不包含"元万元"的情况）
        if '万元' in clean_str and '元万元' not in clean_str:
            # 处理"万元"情况
            number_match = re.search(r'(\d+\.?\d*)万元', clean_str)
            if number_match:
                number_value = float(number_match.group(1))
                return number_value * 10000
        
        # 2. 处理"元万元"情况（直接提取数字，不乘以10000）
        if '元万元' in clean_str:
            number_match = re.search(r'(\d+\.?\d*)', clean_str)
            if number_match:
                number_value = float(number_match.group(1))
                return number_value
        
        # 3. 处理单独的"元"情况
        if '元' in clean_str and '万元' not in clean_str:
            number_match = re.search(r'(\d+\.?\d*)元', clean_str)
            if number_match:
                return float(number_match.group(1))
        
        # 4. 尝试直接解析为数字
        try:
            return float(clean_str)
        except ValueError:
            pass
            
    except Exception as e:
        logger.warning(f'金额转换失败: {price_str}, 错误: {e}')
    
    return None

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
        queryset = ProcurementEmall.objects.all()
        
        # 处理预算控制金额的数字搜索
        price_search_param = self.request.query_params.get('total_price_control_search')
        if price_search_param:
            try:
                search_data = json.loads(price_search_param)
                operator = search_data.get('operator')
                
                # 创建子查询来筛选符合条件的记录
                matching_ids = []
                for item in ProcurementEmall.objects.all():
                    numeric_value = convert_price_to_number(item.total_price_control)
                    if numeric_value is not None:
                        if operator == '>' and numeric_value > search_data.get('value', 0):
                            matching_ids.append(item.id)
                        elif operator == '>=' and numeric_value >= search_data.get('value', 0):
                            matching_ids.append(item.id)
                        elif operator == '<' and numeric_value < search_data.get('value', 0):
                            matching_ids.append(item.id)
                        elif operator == '<=' and numeric_value <= search_data.get('value', 0):
                            matching_ids.append(item.id)
                        elif operator in ('=', '==') and abs(numeric_value - search_data.get('value', 0)) < 0.01:
                            matching_ids.append(item.id)
                        elif operator == 'range' and search_data.get('min') <= numeric_value <= search_data.get('max'):
                            matching_ids.append(item.id)
                
                queryset = queryset.filter(id__in=matching_ids)
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f'预算控制金额搜索参数解析失败: {price_search_param}, 错误: {e}')
        
        # 搜索处理
        search_value = self.request.query_params.get('search', '')
        if not search_value:
            search_value = self.request.query_params.get('search[value]', '')
            
        if search_value:
            queryset = queryset.filter(
                Q(project_title__icontains=search_value) |
                Q(purchasing_unit__icontains=search_value) |
                Q(project_number__icontains=search_value) |
                Q(region__icontains=search_value)
            )
        
        # 排序处理
        ordering = self.request.query_params.get('ordering', '')
        if ordering:
            ordering_fields = ordering.split(',')
            queryset = queryset.order_by(*ordering_fields)
        else:
            # 默认按发布日期降序排列
            queryset = queryset.order_by('-publish_date')
        
        return queryset

class ProcurementDetailView(RetrieveAPIView):
    queryset = ProcurementEmall.objects.all()
    serializer_class = ProcurementEmallSerializer
    lookup_field = 'pk'
