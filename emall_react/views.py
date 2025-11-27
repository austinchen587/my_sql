# emall_react/views.py
from rest_framework import generics, filters
from django_filters.rest_framework import DjangoFilterBackend
from emall.models import ProcurementEmall
from .serializers import EmallListSerializer
from django_filters import FilterSet, CharFilter
from django.db.models import Q
import re

class ProcurementEmallFilter(FilterSet):
    """
    自定义过滤器类，支持项目标题、采购单位、项目编号、控制总价的筛选
    """
    project_title = CharFilter(field_name='project_title', lookup_expr='icontains', label='项目标题')
    purchasing_unit = CharFilter(field_name='purchasing_unit', lookup_expr='icontains', label='采购单位')
    project_number = CharFilter(field_name='project_number', lookup_expr='icontains', label='项目编号')
    total_price_control = CharFilter(field_name='total_price_control', lookup_expr='icontains', label='控制总价')
    
    class Meta:
        model = ProcurementEmall
        fields = ['project_title', 'purchasing_unit', 'project_number', 'total_price_control']

class EmallListView(generics.ListAPIView):
    """
    为React前端提供采购项目列表的API视图
    支持筛选功能：项目标题、采购单位、项目编号、控制总价、价格条件筛选
    """
    queryset = ProcurementEmall.objects.all().order_by('-publish_date', '-id')
    serializer_class = EmallListSerializer
    
    # 配置过滤后端
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # 使用自定义过滤器（精确字段筛选）
    filterset_class = ProcurementEmallFilter
    
    # 搜索字段（全局搜索）
    search_fields = ['project_title', 'purchasing_unit', 'project_number', 'total_price_control']
    
    # 排序字段
    ordering_fields = ['publish_date', 'quote_end_time']
    ordering = ['-publish_date']  # 默认按发布时间倒序

    def get_queryset(self):
        """
        添加价格条件筛选逻辑
        """
        queryset = super().get_queryset()
        
        # 获取价格条件参数
        price_condition = self.request.query_params.get('total_price_condition')
        
        if price_condition:
            # 使用Python进行内存筛选（适用于数据量不大的情况）
            filtered_items = []
            for item in queryset:
                numeric_price = self.get_numeric_price_for_item(item)
                if numeric_price is not None and self.check_price_condition(numeric_price, price_condition):
                    filtered_items.append(item.id)
            
            # 返回筛选后的查询集
            queryset = queryset.filter(id__in=filtered_items)
        
        # 示例：区域筛选
        region = self.request.query_params.get('region')
        if region:
            queryset = queryset.filter(region__icontains=region)
            
        return queryset

    def get_numeric_price_for_item(self, item):
        """
        为单个项目获取数字化价格
        """
        price_str = item.total_price_control
        if not price_str:
            return None
            
        try:
            price_str = str(price_str).strip()
            
            # 提取数字部分
            match = re.search(r'([\d,]+(?:\.\d+)?)', price_str.replace(',', ''))
            if not match:
                return None
                
            number = float(match.group(1).replace(',', ''))
            
            # 判断单位类型
            if '元万元' in price_str:
                return round(number, 2)
            elif '万元' in price_str:
                return round(number * 10000, 2)
            else:
                return None
                
        except (ValueError, TypeError, AttributeError):
            return None

    def check_price_condition(self, numeric_price, price_condition):
        """
        检查价格是否满足条件
        """
        # 解析操作符和数值
        match = re.match(r'^\s*([><]=?|=)\s*(\d+(?:\.\d+)?)\s*$', price_condition.strip())
        
        if not match:
            return False
            
        operator = match.group(1)
        value = float(match.group(2))
        
        if operator == '>' and numeric_price > value:
            return True
        elif operator == '>=' and numeric_price >= value:
            return True
        elif operator == '<' and numeric_price < value:
            return True
        elif operator == '<=' and numeric_price <= value:
            return True
        elif operator == '=' and numeric_price == value:
            return True
            
        return False
