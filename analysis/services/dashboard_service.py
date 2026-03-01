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
        [核心修复]：全面改用 procurement_emall 的 quote_start_time，并使用 Python 精确控制时间边界
        """
        now = timezone.localtime()
        
        # 1. 今天的起止时间 (00:00:00 到 明天 00:00:00)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_start = today_start + timedelta(days=1)
        
        # 2. 本周的起止时间
        week_start = today_start - timedelta(days=now.weekday())
        next_week_start = week_start + timedelta(days=7)
        
        # 3. 本月的起止时间
        month_start = today_start.replace(day=1)
        if month_start.month == 12:
            next_month_start = month_start.replace(year=month_start.year + 1, month=1)
        else:
            next_month_start = month_start.replace(month=month_start.month + 1)
            
        # 4. 本季度的起止时间
        quarter = (now.month - 1) // 3 + 1
        quarter_start_month = 3 * quarter - 2
        quarter_start = today_start.replace(month=quarter_start_month, day=1)
        if quarter == 4:
            next_quarter_start = quarter_start.replace(year=quarter_start.year + 1, month=1)
        else:
            next_quarter_start = quarter_start.replace(month=quarter_start_month + 3)
            
        # 5. 本年的起止时间
        year_start = today_start.replace(month=1, day=1)
        next_year_start = year_start.replace(year=year_start.year + 1)

        # 使用 quote_start_time::timestamp 配合 >= 和 <，实现100%精准的区间截断
        # 增加了 IS NOT NULL AND != '' 过滤，防止爬虫抓取的脏数据导致类型转换报错
        sql = """
        SELECT 
            COUNT(*) FILTER (
                WHERE quote_start_time IS NOT NULL AND quote_start_time != '' AND quote_start_time != '-'
                AND quote_start_time::timestamp >= %s AND quote_start_time::timestamp < %s
            ) as today_count,
            
            COUNT(*) FILTER (
                WHERE quote_start_time IS NOT NULL AND quote_start_time != '' AND quote_start_time != '-'
                AND quote_start_time::timestamp >= %s AND quote_start_time::timestamp < %s
            ) as week_count,
            
            COUNT(*) FILTER (
                WHERE quote_start_time IS NOT NULL AND quote_start_time != '' AND quote_start_time != '-'
                AND quote_start_time::timestamp >= %s AND quote_start_time::timestamp < %s
            ) as month_count,
            
            COUNT(*) FILTER (
                WHERE quote_start_time IS NOT NULL AND quote_start_time != '' AND quote_start_time != '-'
                AND quote_start_time::timestamp >= %s AND quote_start_time::timestamp < %s
            ) as quarter_count,
            
            COUNT(*) FILTER (
                WHERE quote_start_time IS NOT NULL AND quote_start_time != '' AND quote_start_time != '-'
                AND quote_start_time::timestamp >= %s AND quote_start_time::timestamp < %s
            ) as year_count,
            
            COUNT(*) as total_count
        FROM procurement_emall
        """
        
        # 参数严格按顺序对应占位符
        params = [
            today_start, tomorrow_start,
            week_start, next_week_start,
            month_start, next_month_start,
            quarter_start, next_quarter_start,
            year_start, next_year_start
        ]
        
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            row = cursor.fetchone()
            
            columns = ['today_count', 'week_count', 'month_count', 'quarter_count', 'year_count', 'total_count']
            return dict(zip(columns, row))