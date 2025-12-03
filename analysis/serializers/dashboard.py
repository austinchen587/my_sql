from rest_framework import serializers

class DashboardStatsSerializer(serializers.Serializer):
    """仪表盘统计数据序列化器"""
    today_count = serializers.IntegerField()
    week_count = serializers.IntegerField()
    month_count = serializers.IntegerField()
    quarter_count = serializers.IntegerField()
    year_count = serializers.IntegerField()
    total_count = serializers.IntegerField()
