from django.db import connection
from typing import Dict, Any

class DashboardService:
    """仪表盘数据服务类"""
    
    @staticmethod
    def get_procurement_dashboard_stats() -> Dict[str, Any]:
        """
        获取采购项目仪表盘统计数据
        Returns: 包含各时间段统计数据的字典
        """
        sql = """
        SELECT 
            COUNT(*) FILTER (WHERE publish_date = to_char(CURRENT_DATE, 'YYYY.MM.DD')) as today_count,
            COUNT(*) FILTER (WHERE publish_date >= to_char(DATE_TRUNC('week', CURRENT_DATE), 'YYYY.MM.DD') 
                            AND publish_date <= to_char(DATE_TRUNC('week', CURRENT_DATE) + INTERVAL '6 days', 'YYYY.MM.DD')) as week_count,
 COUNT(*) FILTER (WHERE publish_date LIKE to_char(CURRENT_DATE, 'YYYY.MM') || '.%') as month_count,
            COUNT(*) FILTER (WHERE publish_date >= to_char(DATE_TRUNC('quarter', CURRENT_DATE), 'YYYY.MM.DD') 
                            AND publish_date <= to_char(DATE_TRUNC('quarter', CURRENT_DATE) + INTERVAL '3 months' - INTERVAL '1 day', 'YYYY.MM.DD')) as quarter_count,
            COUNT(*) FILTER (WHERE publish_date LIKE to_char(CURRENT_DATE, 'YYYY') || '.%') as year_count,
            COUNT(*) as total_count
        FROM procurement_emall
        """
        
        with connection.cursor() as cursor:
            cursor.execute(sql)
            row = cursor.fetchone()
            
            # 将结果映射到字典
            columns = ['today_count', 'week_count', 'month_count', 'quarter_count', 'year_count', 'total_count']
            result = dict(zip(columns, row))
            
            return result
