from django.db import models
from emall.models import ProcurementEmall

class BiddingProject(models.Model):
    """竞价大厅清洗数据表 - Read Model"""
    
    # ... (常量定义 PROVINCES, ROOT_CATS 等保持不变) ...
    PROVINCES = (('JX', '江西'), ('HN', '湖南'), ('AH', '安徽'), ('ZJ', '浙江'))
    ROOT_CATS = (('goods', '物资'), ('service', '服务'), ('project', '工程'))
    MODES = (('bidding', '竞价'), ('reverse', '反拍'))
    SUB_CATS = (
        ('office', '行政办公耗材'), ('cleaning', '清洁日化用品'),
        ('digital', '数码家电'), ('sports', '体育器材与服装'),
        ('industrial', '专业设备与工业品'), ('food', '食品与饮品'),
        ('service_other', '服务与其他'),
    )

    # --- 关联与核心字段 ---
    source_emall = models.OneToOneField(
        ProcurementEmall, 
        on_delete=models.CASCADE, 
        related_name='bidding_clean', 
        verbose_name="原始源",
        primary_key=True,   # <--- 关键修改
        db_column='id'      # <--- 关键修改
    )
    title = models.CharField(max_length=500, verbose_name="展示标题")
    province = models.CharField(max_length=10, choices=PROVINCES, db_index=True)
    
    # ... (后续字段保持不变) ...
    root_category = models.CharField(max_length=20, choices=ROOT_CATS, db_index=True)
    sub_category = models.CharField(max_length=50, choices=SUB_CATS, null=True, blank=True, db_index=True)
    mode = models.CharField(max_length=20, choices=MODES, default='bidding', db_index=True)

    control_price = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)
    status = models.IntegerField(default=0, db_index=True)

    class Meta:
        db_table = 'bidding_project_cleaned'
        ordering = ['status', 'start_time']
        indexes = [models.Index(fields=['province', 'root_category', 'sub_category'])]

# === [修改 1] 商品清单表 ===
class ProcurementCommodityBrand(models.Model):
    # 【核心修改】不要用 ForeignKey，改用 CharField，直接对应数据库的 varchar 类型
    procurement_id = models.CharField(
        max_length=100, 
        db_column='procurement_id', # 强制指向数据库的这一列
        verbose_name="原始采购ID",
        db_index=True 
    )
    
    item_name = models.CharField(max_length=500, verbose_name="物品名称", null=True)
    specifications = models.TextField(verbose_name="规格参数", null=True)
    suggested_brand = models.CharField(max_length=500, verbose_name="建议品牌", null=True)
    quantity = models.CharField(max_length=100, verbose_name="数量", null=True)
    unit = models.CharField(max_length=50, verbose_name="单位", null=True)
    
    class Meta:
        db_table = 'procurement_commodity_brand'
        managed = False 

# === [修改 2] 结果表 ===
class ProcurementCommodityResult(models.Model):
    brand_id = models.IntegerField(verbose_name="对应清单ID", null=True, blank=True)
    
    # 【核心修改】同样改为 CharField，防止 Django 自动把字符串转成数字导致报错
    procurement_id = models.CharField(
        max_length=100, 
        db_column='procurement_id',
        verbose_name="原始采购ID",
        db_index=True
    )
    
    item_name = models.CharField(max_length=500, null=True)
    specifications = models.TextField(null=True)
    selected_suppliers = models.TextField(null=True)
    selection_reason = models.TextField(null=True)
    model_used = models.CharField(max_length=100, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'procurement_commodity_result'