# emall_react/filters.py
from django_filters import FilterSet, CharFilter, BooleanFilter
from emall.models import ProcurementEmall
from emall_purchasing.models import ProcurementPurchasing

class ProcurementEmallFilter(FilterSet):
    """
    自定义过滤器类，支持项目标题、采购单位、项目编号、控制总价、只看选择项目的筛选
    """
    project_title = CharFilter(field_name='project_title', lookup_expr='icontains', label='项目标题')
    purchasing_unit = CharFilter(field_name='purchasing_unit', lookup_expr='icontains', label='采购单位')
    project_number = CharFilter(field_name='project_number', lookup_expr='icontains', label='项目编号')
    total_price_control = CharFilter(field_name='total_price_control', lookup_expr='icontains', label='控制总价')
    show_selected_only = BooleanFilter(method='filter_selected_only', label='只看选择项目')
    project_owner = CharFilter(method='filter_project_owner', label='项目归属人')  # 新增
    
    class Meta:
        model = ProcurementEmall
        fields = ['project_title', 'purchasing_unit', 'project_number', 'total_price_control', 'show_selected_only', 'project_owner']
    
    def filter_selected_only(self, queryset, name, value):
        """只看选择项目的筛选逻辑"""
        if value:
            # 获取所有被选中的项目ID
            selected_ids = ProcurementPurchasing.objects.filter(
                is_selected=True
            ).values_list('procurement_id', flat=True)
            return queryset.filter(id__in=selected_ids)
        return queryset
    
    def filter_project_owner(self, queryset, name, value):
        """项目归属人筛选逻辑"""
        if value:
            try:
                import urllib.parse
                decoded_value = urllib.parse.unquote(value)
                selected_ids = ProcurementPurchasing.objects.filter(
                    project_owner__icontains=decoded_value.strip()
                ).values_list('procurement_id', flat=True)
                return queryset.filter(id__in=selected_ids)
            except Exception:
                return queryset
        return queryset
