from django.db import models

class DashboardStats(models.Model):
    """仪表盘统计数据模型（主要用于类型定义）"""
    today_count = models.IntegerField(default=0)
    week_count = models.IntegerField(default=0)
    month_count = models.IntegerField(default=0)
    quarter_count = models.IntegerField(default=0)
    year_count = models.IntegerField(default=0)
    total_count = models.IntegerField(default=0)
    
    class Meta:
        # 这是一个虚拟模型，不需要数据库表
        managed = False

