# analysis/serializers/project_profit_stats.py
from rest_framework import serializers
from ..models.project_profit_stats import ProjectProfitStats

class ProjectProfitStatsSerializer(serializers.ModelSerializer):
    """项目利润统计序列化器"""
    
    class Meta:
        model = ProjectProfitStats
        fields = [
            'project_name',
            'start_time',
            'end_time',
            'project_status',
            'project_owner',
            'expected_total_price',
            'response_total',
            'winning_date',
            'settlement_amount',
            'settlement_date',
            'final_quote',
            'purchase_payment_amount',
            'procurement_id',
            'project_number',
            'bid_cycle_days',
            'settlement_cycle_days',
            'project_profit',
            'project_profit_margin',
            'statistics_month'
        ]
