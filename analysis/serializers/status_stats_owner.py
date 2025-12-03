from rest_framework import serializers

class ProcurementStatusStatsOwnerSerializer(serializers.Serializer):
    """采购项目按归属人竞标状态统计序列化器"""
    status = serializers.CharField()
    status_display = serializers.CharField()
    today = serializers.IntegerField()
    week = serializers.IntegerField()
    month = serializers.IntegerField()
    year = serializers.IntegerField()
    total = serializers.IntegerField()
