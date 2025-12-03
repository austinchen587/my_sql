from django.db import models

class ProcurementStatusStatsOwner(models.Model):
    """采购项目按归属人竞标状态统计模型"""
    status = models.CharField(max_length=20)
    status_display = models.CharField(max_length=50)
    today = models.IntegerField(default=0)
    week = models.IntegerField(default=0)
    month = models.IntegerField(default=0)
    year = models.IntegerField(default=0)
    total = models.IntegerField(default=0)
    
    class Meta:
        # 这是一个虚拟模型，不需要数据库表
        managed = False
