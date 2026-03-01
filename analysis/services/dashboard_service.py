from django.db import connection
from django.utils import timezone
from datetime import timedelta
from typing import Dict, Any

class DashboardService:
    """仪表盘数据服务类"""
    
    @staticmethod
    def get_procurement_dashboard_stats() -> Dict[str, Any]:
        """
        获取采购项目仪表盘统计数据
        Returns: 包含各时间段统计数据的字典
        """
        # [核心修复]：在 Python 端计算本地时区的准确日期，避免数据库 UTC 时区干扰
        now = timezone.localtime()
        
        # 1. 今天的日期字符串：'2026.03.01'
        today_str = now.strftime('%Y.%m.%d')
        
        # 2. 本周的起始和结束日期字符串
        week_start = now - timedelta(days=now.weekday())
        week_end = week_start + timedelta(days=6)
        week_start_str = week_start.strftime('%Y.%m.%d')
        week_end_str = week_end.strftime('%Y.%m.%d')
        
        # 3. 本月的匹配前缀：'2026.03.%'
        month_prefix = now.strftime('%Y.%m.')
        
        # 4. 本季度的起始和结束日期
        quarter = (now.month - 1) // 3 + 1
        quarter_start_month = 3 * quarter - 2
        quarter_start_date = now.replace(month=quarter_start_month, day=1)
        if quarter == 4:
            quarter_end_date = now.replace(year=now.year+1, month=1, day=1) - timedelta(days=1)
        else:
            quarter_end_date = now.replace(month=quarter_start_month+3, day=1) - timedelta(days=1)
            
        quarter_start_str = quarter_start_date.strftime('%Y.%m.%d')
        quarter_end_str = quarter_end_date.strftime('%Y.%m.%d')
        
        # 5. 本年的匹配前缀：'2026.%'
        year_prefix = now.strftime('%Y.')

        # 将动态计算的本地时间参数传入 SQL
        sql = """
        SELECT 
            COUNT(*) FILTER (WHERE publish_date = %s) as today_count,
            COUNT(*) FILTER (WHERE publish_date >= %s AND publish_date <= %s) as week_count,
            COUNT(*) FILTER (WHERE publish_date LIKE %s) as month_count,
            COUNT(*) FILTER (WHERE publish_date >= %s AND publish_date <= %s) as quarter_count,
            COUNT(*) FILTER (WHERE publish_date LIKE %s) as year_count,
            COUNT(*) as total_count
        FROM procurement_emall
        """
        
        params = [
            today_str,
            week_start_str, week_end_str,
            f"{month_prefix}%",
            quarter_start_str, quarter_end_str,
            f"{year_prefix}%"
        ]
        
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            row = cursor.fetchone()
            
            # 将结果映射到字典
            columns = ['today_count', 'week_count', 'month_count', 'quarter_count', 'year_count', 'total_count']
            result = dict(zip(columns, row))
            
            return result