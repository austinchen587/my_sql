# analysis/models/daily_profit_stats.py
from django.db import models

class DailyProfitStats(models.Model):
    """每日利润统计模型"""
    project_name = models.CharField(max_length=255)
    project_owner = models.CharField(max_length=100)
    total_price_control = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    supplier_name = models.CharField(max_length=255)
    total_quote = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    final_negotiated_quote = models.DecimalField(max_digits=15, decimal_places=2, default=0)  # 新增字段
    profit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    latest_remark = models.TextField(blank=True, null=True)
    
    class Meta:
        # 这是一个虚拟模型，不需要数据库表
        managed = False
