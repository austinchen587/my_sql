from django.db import models
from emall.models import ProcurementEmall

class ProcurementPurchasing(models.Model):
    procurement = models.OneToOneField(
        ProcurementEmall, 
        on_delete=models.CASCADE, 
        related_name='purchasing_info'
    )
    is_selected = models.BooleanField(default=False, verbose_name='是否选择采购')
    
    # 采购进度相关字段
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
