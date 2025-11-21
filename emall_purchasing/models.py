from django.db import models
from django.contrib.postgres.fields import ArrayField
import re  # 导入正则表达式模块
from emall.models import ProcurementEmall

class Supplier(models.Model):
    """供应商模型"""
    name = models.CharField(max_length=255, verbose_name='供应商名称')
    source = models.CharField(max_length=255, null=True, blank=True,verbose_name='获取渠道')
    contact = models.CharField(max_length=255, null=True, blank=True, verbose_name='联系方式')
    store_name = models.CharField(max_length=255, null=True, blank=True, verbose_name='店铺名称')
    
    class Meta:
        db_table = 'procurement_suppliers'  # 改为复数形式，避免冲突
        verbose_name = '供应商'
        verbose_name_plural = '供应商'

    def __str__(self):
        return self.name

class SupplierCommodity(models.Model):
    """供应商商品信息"""
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='commodities')
    name = models.CharField(max_length=255, verbose_name='商品名称')
    specification = models.TextField(null=True, blank=True, verbose_name='商品规格')
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='价格')
    quantity = models.IntegerField(verbose_name='数量')
    product_url = models.URLField(max_length=500, null=True, blank=True, verbose_name='产品链接')
    
    class Meta:
        db_table = 'supplier_commodities'  # 改为复数形式
        verbose_name = '供应商商品'
        verbose_name_plural = '供应商商品'

    def __str__(self):
        return f"{self.supplier.name} - {self.name}"

class ProcurementPurchasing(models.Model):
    # 竞标状态选项
    BIDDING_STATUS_CHOICES = [
        ('not_started', '未开始'),
        ('in_progress', '进行中'),
        ('successful', '竞标成功'),
        ('failed', '竞标失败'),
        ('cancelled', '已取消'),
    ]
    
    procurement = models.OneToOneField(
        ProcurementEmall, 
        on_delete=models.CASCADE, 
        related_name='purchasing_info'
    )
    is_selected = models.BooleanField(default=False, verbose_name='是否选择采购')
    
    # 竞标状态
    bidding_status = models.CharField(
        max_length=20, 
        choices=BIDDING_STATUS_CHOICES, 
        default='not_started',
        verbose_name='竞标状态'
    )
    
    # 甲方信息
    client_contact = models.CharField(max_length=255, null=True, blank=True, verbose_name='甲方联系人')
    client_phone = models.CharField(max_length=255, null=True, blank=True, verbose_name='甲方联系方式')
    
    # 关联供应商（支持多个供应商）
    suppliers = models.ManyToManyField(Supplier, through='ProcurementSupplier', related_name='procurements')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'procurement_purchasing'
        verbose_name = '采购进度管理'
        verbose_name_plural = '采购进度管理'

    def __str__(self):
        return f"{self.procurement.project_title} - 采购信息"
    
    def get_total_budget(self):
        """获取项目总预算"""
        if self.procurement.total_price_control:
            # 使用之前的金额转换逻辑
            return self.convert_price_to_number(self.procurement.total_price_control)
        return 0
    
    def convert_price_to_number(self, price_str):
        """金额转换方法 - 修正版本"""
        if not price_str or price_str == '-': 
            return 0
        try:
            # 使用Python的字符串替换方法
            clean_str = price_str.replace(' ', '').replace(',', '')
            
            # 使用Python的正则表达式
            if '万元' in clean_str and '元万元' not in clean_str:
                match = re.search(r'(\d+\.?\d*)\s*万元', price_str)
                if match:
                    return float(match.group(1)) * 10000
            
            if '元万元' in clean_str:
                match = re.search(r'(\d+\.?\d*)', clean_str)
                if match:
                    return float(match.group(1))
            
            if '元' in clean_str and '万元' not in clean_str:
                match = re.search(r'(\d+\.?\d*)\s*元', price_str)
                if match:
                    return float(match.group(1))
            
            # 如果没有单位，尝试直接解析为数字
            try:
                return float(clean_str)
            except ValueError:
                return 0
                
        except Exception as e:
            print(f"金额转换错误: {e}")
            return 0
    
    def get_suppliers_info(self):
        """获取供应商信息（包含利润计算）"""
        suppliers_info = []
        for procurement_supplier in self.procurementsupplier_set.all():
            supplier = procurement_supplier.supplier
            total_quote = procurement_supplier.get_total_quote()
            budget = self.get_total_budget()
            profit = budget - total_quote if budget > 0 else 0
            
            suppliers_info.append({
                'id': supplier.id,
                'name': supplier.name,
                'source': supplier.source,
                'contact': supplier.contact,
                'store_name': supplier.store_name,
                'total_quote': float(total_quote) if total_quote else 0,
                'profit': profit,
                'is_selected': procurement_supplier.is_selected,
                'commodities': [
                    {
                        'name': commodity.name,
                        'specification': commodity.specification or '',
                        'price': float(commodity.price) if commodity.price else 0,
                        'quantity': commodity.quantity or 0
                    }
                    for commodity in supplier.commodities.all()
                ]
            })
        return suppliers_info

class ProcurementSupplier(models.Model):
    """采购项目与供应商关联表"""
    procurement = models.ForeignKey(ProcurementPurchasing, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    is_selected = models.BooleanField(default=False, verbose_name='是否选择该供应商')
    
    class Meta:
        db_table = 'procurement_supplier_relation'  # 改为不同的表名
        unique_together = ('procurement', 'supplier')
        verbose_name = '采购供应商关系'
        verbose_name_plural = '采购供应商关系'

    def get_total_quote(self):
        """获取该供应商的总报价"""
        total = 0
        for commodity in self.supplier.commodities.all():
            if commodity.price and commodity.quantity:
                total += commodity.price * commodity.quantity
        return total

class ProcurementRemark(models.Model):
    """采购备注历史记录"""
    purchasing = models.ForeignKey(
        ProcurementPurchasing, 
        on_delete=models.CASCADE, 
        related_name='remarks_history'
    )
    remark_content = models.TextField(verbose_name='备注内容')
    created_by = models.CharField(max_length=100, verbose_name='创建人')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'procurement_purchasing_remarks'
        verbose_name = '采购备注记录'
        verbose_name_plural = '采购备注记录'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.purchasing.procurement.project_title} - 备注"
