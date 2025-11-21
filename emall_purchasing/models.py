from django.db import models
from django.contrib.postgres.fields import ArrayField
from emall.models import ProcurementEmall

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
    
    # 新增的商品信息字段（数组字段，支持多个商品）
    commodity_names = ArrayField(
        models.CharField(max_length=255, blank=True), 
        null=True, blank=True, 
        verbose_name='商品名'
    )
    product_specifications = ArrayField(
        models.CharField(max_length=500, blank=True), 
        null=True, blank=True, 
        verbose_name='产品规格'
    )
    prices = ArrayField(
        models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True), 
        null=True, blank=True, 
        verbose_name='价格'
    )
    quantities = ArrayField(
        models.IntegerField(blank=True, null=True), 
        null=True, blank=True, 
        verbose_name='数量'
    )
    product_urls = ArrayField(
        models.URLField(max_length=500, blank=True), 
        null=True, blank=True, 
        verbose_name='产品链接'
    )
    
    # 竞标状态
    bidding_status = models.CharField(
        max_length=20, 
        choices=BIDDING_STATUS_CHOICES, 
        default='not_started',
        verbose_name='竞标状态'
    )
    
    # 备注说明
    remarks = models.TextField(null=True, blank=True, verbose_name='备注说明')
    
    # 原有的采购进度相关字段（保持不变）
    client_contact = models.CharField(max_length=255, null=True, blank=True, verbose_name='甲方联系人')
    client_phone = models.CharField(max_length=255, null=True, blank=True, verbose_name='甲方联系方式')
    supplier_source = models.CharField(max_length=255, null=True, blank=True, verbose_name='供应商获取渠道')
    supplier_store = models.CharField(max_length=255, null=True, blank=True, verbose_name='供应商店铺名称')
    supplier_contact = models.CharField(max_length=255, null=True, blank=True, verbose_name='供应商联系方式')
    cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='成本')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'procurement_purchasing'
        verbose_name = '采购进度管理'
        verbose_name_plural = '采购进度管理'

    def __str__(self):
        return f"{self.procurement.project_title} - 采购信息"
    
    def get_commodities_count(self):
        """获取商品数量"""
        if self.commodity_names:
            return len(self.commodity_names)
        return 0
    
    def get_total_amount(self):
        """计算总金额"""
        if self.prices and self.quantities:
            total = 0
            for i in range(min(len(self.prices), len(self.quantities))):
                price = self.prices[i] or 0
                quantity = self.quantities[i] or 0
                total += price * quantity
            return total
        return 0
    
    def get_commodities_info(self):
        """获取商品信息列表"""
        commodities = []
        if self.commodity_names:
            for i in range(len(self.commodity_names)):
                commodity_info = {
                    'name': self.commodity_names[i] if i < len(self.commodity_names) else '',
                    'specification': self.product_specifications[i] if self.product_specifications and i < len(self.product_specifications) else '',
                    'price': float(self.prices[i]) if self.prices and i < len(self.prices) and self.prices[i] is not None else None,
                    'quantity': self.quantities[i] if self.quantities and i < len(self.quantities) else None,
                    'url': self.product_urls[i] if self.product_urls and i < len(self.product_urls) else ''
                }
                commodities.append(commodity_info)
        return commodities



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
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'procurement_purchasing_remarks'
        verbose_name = '采购备注记录'
        verbose_name_plural = '采购备注记录'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.purchasing.procurement.project_title} - 备注({self.created_at})"
