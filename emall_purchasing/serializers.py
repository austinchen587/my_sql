# emall_purchasing/serializers.py
from rest_framework import serializers
from .models import ProcurementPurchasing, ProcurementRemark, Supplier, SupplierCommodity, ProcurementSupplier, UnifiedProcurementRemark
from emall.models import ProcurementEmall  # 从emall应用导入

class SupplierCommoditySerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierCommodity
        fields = [
            'id', 'name', 'specification', 'price', 'quantity', 'product_url',
            'purchaser_created_by', 'purchaser_created_role'  # 新增审计字段
        ]
        read_only_fields = ('purchaser_created_by', 'purchaser_created_role')  # 审计字段只读

class SupplierSerializer(serializers.ModelSerializer):
    commodities = SupplierCommoditySerializer(many=True, read_only=True)
    total_quote = serializers.SerializerMethodField()
    
    class Meta:
        model = Supplier
        fields = [
            'id', 'name', 'source', 'contact', 'store_name', 'commodities', 'total_quote',
            'purchaser_created_by', 'purchaser_created_role',  # 新增审计字段
            'purchaser_updated_by', 'purchaser_updated_role'   # 新增审计字段
        ]
        read_only_fields = (
            'purchaser_created_by', 'purchaser_created_role',  # 审计字段只读
            'purchaser_updated_by', 'purchaser_updated_role'
        )
    
    def get_total_quote(self, obj):
        total = 0
        for commodity in obj.commodities.all():
            total += commodity.price * commodity.quantity
        return total

class ProcurementSupplierSerializer(serializers.ModelSerializer):
    supplier = SupplierSerializer(read_only=True)
    total_quote = serializers.ReadOnlyField(source='get_total_quote')
    
    class Meta:
        model = ProcurementSupplier
        fields = [
            'id', 'supplier', 'is_selected', 'total_quote',
            'purchaser_created_by', 'purchaser_created_role',  # 新增审计字段
            'purchaser_updated_by', 'purchaser_updated_role'   # 新增审计字段
        ]
        read_only_fields = (
            'purchaser_created_by', 'purchaser_created_role',  # 审计字段只读
            'purchaser_updated_by', 'purchaser_updated_role'
        )

class ProcurementRemarkSerializer(serializers.ModelSerializer):
    created_at_display = serializers.DateTimeField(source='created_at', format='%Y-%m-%d %H:%M', read_only=True)
    
    class Meta:
        model = ProcurementRemark
        fields = ['id', 'remark_content', 'created_by', 'created_at', 'created_at_display']

class UnifiedProcurementRemarkSerializer(serializers.ModelSerializer):
    """统一采购备注序列化器"""
    created_at_display = serializers.SerializerMethodField()
    remark_type_display = serializers.CharField(source='get_remark_type_display', read_only=True)
    procurement_title = serializers.CharField(source='procurement.project_title', read_only=True)
    procurement_number = serializers.CharField(source='procurement.project_number', read_only=True)
    
    class Meta:
        model = UnifiedProcurementRemark
        fields = [
            'id', 'procurement', 'procurement_title', 'procurement_number',
            'remark_content', 'created_by', 'remark_type', 'remark_type_display',
            'purchasing', 'created_at', 'created_at_display', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_created_at_display(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S') if obj.created_at else ''

class ProcurementPurchasingSerializer(serializers.ModelSerializer):
    procurement_title = serializers.CharField(source='procurement.project_title', read_only=True)
    procurement_number = serializers.CharField(source='procurement.project_number', read_only=True)
    total_budget = serializers.SerializerMethodField()
    suppliers_info = serializers.SerializerMethodField()
    bidding_status_display = serializers.CharField(source='get_bidding_status_display', read_only=True)
    remarks_history = ProcurementRemarkSerializer(many=True, read_only=True)
    project_owner = serializers.CharField(read_only=True)
    
    class Meta:
        model = ProcurementPurchasing
        fields = [
            'id', 'procurement_id', 'is_selected', 'bidding_status', 'bidding_status_display',
            'procurement_title', 'procurement_number', 'total_budget', 'suppliers_info', 
            'remarks_history', 'created_at', 'updated_at', 'project_owner'
        ]
    
    def get_total_budget(self, obj):
        return obj.get_total_budget()
    
    def get_suppliers_info(self, obj):
        """获取供应商信息，包含审计字段"""
        suppliers_info = []
        
        # 计算所有被选中供应商的总报价
        total_selected_quote = 0
        selected_supplier_ids = []
        
        # 先计算总报价
        for procurement_supplier in obj.procurementsupplier_set.all():
            supplier = procurement_supplier.supplier
            total_quote = procurement_supplier.get_total_quote()
            
            if procurement_supplier.is_selected:
                total_selected_quote += total_quote
                selected_supplier_ids.append(supplier.id)
        
        # 计算总利润
        budget = obj.get_total_budget()
        total_profit = budget - total_selected_quote if budget > 0 else 0
        
        # 构建供应商信息
        for procurement_supplier in obj.procurementsupplier_set.all():
            supplier = procurement_supplier.supplier
            supplier_quote = procurement_supplier.get_total_quote()
            
            supplier_data = {
                'id': supplier.id,
                'name': supplier.name,
                'source': supplier.source,
                'contact': supplier.contact,
                'store_name': supplier.store_name,
                'total_quote': float(supplier_quote) if supplier_quote else 0,
                'is_selected': procurement_supplier.is_selected,
                # 新增审计字段
                'purchaser_created_by': supplier.purchaser_created_by,
                'purchaser_created_role': supplier.purchaser_created_role,
                'purchaser_updated_by': supplier.purchaser_updated_by,
                'purchaser_updated_role': supplier.purchaser_updated_role,
                'supplier_relation_info': {
                    'purchaser_created_by': procurement_supplier.purchaser_created_by,
                    'purchaser_created_role': procurement_supplier.purchaser_created_role,
                    'purchaser_updated_by': procurement_supplier.purchaser_updated_by,
                    'purchaser_updated_role': procurement_supplier.purchaser_updated_role,
                },
                'commodities': [
                    {
                        'name': commodity.name,
                        'specification': commodity.specification or '',
                        'price': float(commodity.price) if commodity.price else 0,
                        'quantity': commodity.quantity or 0,
                        'product_url': commodity.product_url or '',
                        # 商品审计字段
                        'purchaser_created_by': commodity.purchaser_created_by,
                        'purchaser_created_role': commodity.purchaser_created_role,
                    }
                    for commodity in supplier.commodities.all()
                ]
            }
            
            # 利润计算：如果是被选中的供应商，显示总利润；否则利润为0
            if procurement_supplier.is_selected:
                supplier_data['profit'] = float(total_profit) if total_profit > 0 else 0
            else:
                supplier_data['profit'] = 0
                
            suppliers_info.append(supplier_data)
        
        return suppliers_info

# 新增：供应商创建和更新的序列化器
class SupplierCreateSerializer(serializers.ModelSerializer):
    """供应商创建序列化器"""
    commodities = SupplierCommoditySerializer(many=True, required=False)
    
    class Meta:
        model = Supplier
        fields = [
            'name', 'source', 'contact', 'store_name', 'commodities',
            'purchaser_created_by', 'purchaser_created_role'  # 审计字段
        ]
        read_only_fields = ('purchaser_created_by', 'purchaser_created_role')  # 审计字段只读

class SupplierUpdateSerializer(serializers.ModelSerializer):
    """供应商更新序列化器"""
    commodities = SupplierCommoditySerializer(many=True, required=False)
    
    class Meta:
        model = Supplier
        fields = [
            'name', 'source', 'contact', 'store_name', 'commodities',
            'purchaser_updated_by', 'purchaser_updated_role'  # 审计字段
        ]
        read_only_fields = ('purchaser_updated_by', 'purchaser_updated_role')  # 审计字段只读

class ProcurementSupplierCreateSerializer(serializers.ModelSerializer):
    """采购供应商关系创建序列化器"""
    class Meta:
        model = ProcurementSupplier
        fields = ['procurement', 'supplier', 'is_selected', 'purchaser_created_by', 'purchaser_created_role']
        read_only_fields = ('purchaser_created_by', 'purchaser_created_role')  # 审计字段只读
