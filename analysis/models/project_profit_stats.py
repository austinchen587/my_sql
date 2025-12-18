# analysis/models/project_profit_stats.py
from django.db import models

class ProjectProfitStats(models.Model):
    """项目利润统计模型"""
    project_name = models.CharField(max_length=255)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    project_status = models.CharField(max_length=50)
    project_owner = models.CharField(max_length=100)
    expected_total_price = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    response_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    winning_date = models.DateTimeField(null=True, blank=True)
    settlement_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    settlement_date = models.DateTimeField(null=True, blank=True)
    final_quote = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    purchase_payment_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    procurement_id = models.IntegerField()
    project_number = models.CharField(max_length=255)
    bid_cycle_days = models.IntegerField(default=0)
    settlement_cycle_days = models.IntegerField(default=0)
    project_profit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    project_profit_margin = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    statistics_month = models.CharField(max_length=7)
    
    class Meta:
        managed = False
