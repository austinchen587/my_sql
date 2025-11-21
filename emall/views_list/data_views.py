from django.db.models import Q
from django_filters import rest_framework as filters
from rest_framework.generics import ListAPIView, RetrieveAPIView
from .pagination import DataTablesPagination
from .filters import ProcurementEmallFilter
from .utils import convert_price_to_number
from ..models import ProcurementEmall
from ..serializers import ProcurementEmallSerializer
import logging
import json

logger = logging.getLogger(__name__)

class ProcurementListDataView(ListAPIView):
    """采购列表数据视图"""
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
                        elif operator == 'range' and search_data.get('min', 0) <= numeric_value <= search_data.get('max', 0):
                            matching_ids.append(item.id)
                
                queryset = queryset.filter(id__in=matching_ids)
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f'预算控制金额搜索参数解析失败: {price_search_param}, 错误: {e}')
        
        # 搜索处理 - 移除地区搜索
        search_value = self.request.query_params.get('search', '')
        if not search_value:
            search_value = self.request.query_params.get('search[value]', '')
            
        if search_value:
            queryset = queryset.filter(
                Q(project_title__icontains=search_value) |
                Q(purchasing_unit__icontains=search_value) |
                Q(project_number__icontains=search_value)
                # 移除地区搜索: Q(region__icontains=search_value)
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
    """采购详情视图"""
    queryset = ProcurementEmall.objects.all()
    serializer_class = ProcurementEmallSerializer
    lookup_field = 'pk'
