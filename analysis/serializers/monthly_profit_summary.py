# analysis/serializers/monthly_profit_summary.py
from rest_framework import serializers
from ..models.monthly_profit_summary import MonthlyProfitSummary

class MonthlyProfitSummarySerializer(serializers.ModelSerializer):
    """月度利润汇总序列化器"""
    
    class Meta:
        model = MonthlyProfitSummary
        fields = [
            'statistics_month',
            'project_count',
            'total_response_amount',
            'total_purchase_amount',
            'total_profit',
            'total_profit_margin',
            'settlement_fund_rate',
            'avg_bid_cycle',
            'avg_settlement_cycle'
        ]
