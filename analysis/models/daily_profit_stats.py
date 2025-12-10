# analysis/models/daily_profit_stats.py
from django.db import models

class DailyProfitStats(models.Model):
    """每日利润统计模型"""
    project_name = models.CharField(max_length=255)
    project_owner = models.CharField(max_length=100)
    total_price_control = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    supplier_name = models.CharField(max_length=255)
    total_quote = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    final_negotiated_quote = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    profit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    latest_remark = models.TextField(blank=True, null=True)
    selected_at = models.DateTimeField(null=True, blank=True)  # 新增字段，记录选中时间
    is_selected = models.BooleanField(default=False)  # 新增字段，是否被选中
    
    class Meta:
        managed = False
