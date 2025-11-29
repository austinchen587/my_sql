# emall/views_list/data_views.py
import logging
import json
from django.db.models import Q
from django_filters import rest_framework as filters
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework import status
from .pagination import DataTablesPagination
from .filters import ProcurementEmallFilter
from .utils import convert_price_to_number
from ..models import ProcurementEmall
from emall_purchasing.models import ProcurementPurchasing
from ..serializers import ProcurementEmallSerializer

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
        if show_selected_only and show_selected_only.lower() in ['true', '1', 'yes']:
            try:
                selected_procurements = ProcurementPurchasing.objects.filter(
                    is_selected=True
                ).values_list('procurement_id', flat=True)
                queryset = queryset.filter(id__in=selected_procurements)
            except Exception as e:
                logger.error(f"筛选已选择项目时出错: {e}")
        
        # 处理预算控制金额的数字搜索
        price_search_param = self.request.query_params.get('total_price_control_search')
        if price_search_param:
            try:
                search_data = json.loads(price_search_param)
                operator = search_data.get('operator')
                
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
        
        return queryset

    def get_serializer_context(self):
        """为序列化器提供采购进度信息映射表"""
        context = super().get_serializer_context()
        
        # 获取当前页面的所有采购项目ID
        procurement_ids = list(self.get_queryset().values_list('id', flat=True))
        
        # 批量查询对应的采购进度信息
        purchasing_infos = ProcurementPurchasing.objects.filter(
            procurement_id__in=procurement_ids
        )
        
        # 创建映射表：{procurement_id: purchasing_info}
        purchasing_map = {}
        for info in purchasing_infos:
            purchasing_map[info.procurement_id] = info
        
        context['purchasing_info_map'] = purchasing_map
        return context

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
    def retrieve(self, request, *args, **kwargs):
        """重写retrieve方法，确保返回前端需要的数据结构"""
        try:
            instance = self.get_object()
            
            # 调试实例的数组字段
            print(f"\n🎯 实例数组字段原始值:")
            print(f"📦 commodity_names: {instance.commodity_names} (类型: {type(instance.commodity_names)})")
            print(f"📦 parameter_requirements: {instance.parameter_requirements}")
            print(f"📦 purchase_quantities: {instance.purchase_quantities}")
            print(f"📦 control_amounts: {instance.control_amounts}")
            print(f"📦 suggested_brands: {instance.suggested_brands}")
            print(f"📦 business_items: {instance.business_items}")
            print(f"📦 business_requirements: {instance.business_requirements}")
            print(f"📦 related_links: {instance.related_links}")
            print(f"📦 download_files: {instance.download_files}")
            
            serializer = self.get_serializer(instance)
            response_data = serializer.data
            
            # 调试序列化后的数据
            print(f"\n📋 序列化后数据包含字段: {list(response_data.keys())}")
            
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"获取详情失败: {e}")
            return Response(
                {'error': '获取项目详情失败'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )