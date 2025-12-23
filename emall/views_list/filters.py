from django_filters import rest_framework as filters
from ..models import ProcurementEmall

class ProcurementEmallFilter(filters.FilterSet):
    """采购数据过滤器"""
    project_title = filters.CharFilter(lookup_expr='icontains')
    purchasing_unit = filters.CharFilter(lookup_expr='icontains')
    project_number = filters.CharFilter(lookup_expr='icontains')  # 添加项目编号过滤器
    total_price_control = filters.CharFilter(lookup_expr='icontains')
    region = filters.CharFilter(lookup_expr='icontains')
    
    class Meta:
        model = ProcurementEmall
        fields = ['project_title', 'purchasing_unit', 'project_number', 'total_price_control', 'region']
        # 移除地区: fields = ['project_title', 'purchasing_unit', 'total_price_control', 'region']
