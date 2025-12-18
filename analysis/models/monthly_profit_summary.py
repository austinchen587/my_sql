# analysis/models/monthly_profit_summary.py
from django.db import models

class MonthlyProfitSummary(models.Model):
    """月度利润汇总模型"""
    statistics_month = models.CharField(max_length=7)
    project_count = models.IntegerField()
    total_response_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_purchase_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_profit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_profit_margin = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    settlement_fund_rate = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    avg_bid_cycle = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    avg_settlement_cycle = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        managed = False
