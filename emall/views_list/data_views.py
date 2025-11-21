# data_views.py
from django.db.models import Q, Exists, OuterRef
from django_filters import rest_framework as filters
from rest_framework.generics import ListAPIView, RetrieveAPIView
from .pagination import DataTablesPagination
from .filters import ProcurementEmallFilter
from .utils import convert_price_to_number
from ..models import ProcurementEmall
from emall_purchasing.models import ProcurementPurchasing  # 导入采购进度模型
from emall_purchasing.serializers import ProcurementPurchasingSerializer  # 导入序列化器
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
        
        # 处理只看已选择项目的筛选
        show_selected_only = self.request.query_params.get('show_selected_only')
        logger.info(f"show_selected_only参数: {show_selected_only}")
        
        if show_selected_only and show_selected_only.lower() in ['true', '1', 'yes']:
            try:
                # 方法1: 使用子查询筛选已选择的项目
                selected_procurements = ProcurementPurchasing.objects.filter(
                    is_selected=True
                ).values_list('procurement_id', flat=True)
                
                queryset = queryset.filter(id__in=selected_procurements)
                logger.info(f"筛选已选择项目，共 {queryset.count()} 条记录")
                
                # 方法2: 使用Exists子查询（性能更好）
                # queryset = queryset.filter(
                #     Exists(ProcurementPurchasing.objects.filter(
                #         procurement_id=OuterRef('id'),
                #         is_selected=True
                #     ))
                # )
                
            except Exception as e:
                logger.error(f"筛选已选择项目时出错: {e}")
        
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
        
        # 搜索处理
        search_value = self.request.query_params.get('search', '')
        if not search_value:
            search_value = self.request.query_params.get('search[value]', '')
            
        if search_value:
            queryset = queryset.filter(
                Q(project_title__icontains=search_value) |
                Q(purchasing_unit__icontains=search_value) |
                Q(project_number__icontains=search_value)
            )
        
        # 排序处理
        ordering = self.request.query_params.get('ordering', '')
        if ordering:
            ordering_fields = ordering.split(',')
            queryset = queryset.order_by(*ordering_fields)
        else:
            # 默认按发布日期降序排列
            queryset = queryset.order_by('-publish_date')
        
        logger.info(f"最终查询集数量: {queryset.count()}")
        return queryset

    def get_serializer_context(self):
        """为序列化器提供额外上下文"""
        context = super().get_serializer_context()
        context['purchasing_info_map'] = self._get_purchasing_info_map()
        return context
    
    def _get_purchasing_info_map(self):
        """获取采购信息映射表，优化性能"""
        # 获取当前页面的采购项目ID
        procurement_ids = list(self.get_queryset().values_list('id', flat=True))
        
        # 批量查询采购信息
        purchasing_infos = ProcurementPurchasing.objects.filter(
            procurement_id__in=procurement_ids
        )
        
        # 创建映射表：{procurement_id: purchasing_info}
        purchasing_map = {}
        for info in purchasing_infos:
            purchasing_map[info.procurement_id] = info
        
        return purchasing_map

class ProcurementDetailView(RetrieveAPIView):
    """采购详情视图"""
    queryset = ProcurementEmall.objects.all()
    serializer_class = ProcurementEmallSerializer
    lookup_field = 'pk'

    def get_serializer_context(self):
        """为序列化器提供额外上下文"""
        context = super().get_serializer_context()
        
        # 为详情页获取采购信息
        try:
            purchasing_info = ProcurementPurchasing.objects.get(
                procurement_id=self.kwargs['pk']
            )
            context['purchasing_info'] = purchasing_info
        except ProcurementPurchasing.DoesNotExist:
            context['purchasing_info'] = None
        
        return context
