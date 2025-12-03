from rest_framework import serializers
from ..models.daily_profit_stats import DailyProfitStats

class DailyProfitStatsSerializer(serializers.ModelSerializer):
    """每日利润统计序列化器"""
    
    class Meta:
        model = DailyProfitStats
        fields = [
            'project_name',
            'project_owner',
            'total_price_control',
            'supplier_name',
            'total_quote',
            'profit',
            'latest_remark'
        ]
