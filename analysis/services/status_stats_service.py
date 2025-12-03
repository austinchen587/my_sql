from django.db import connection
from typing import Dict, Any, List

class StatusStatsService:
    """状态统计数据服务类"""
    
    @staticmethod
    def get_procurement_status_stats() -> List[Dict[str, Any]]:
        """
        按时间维度和竞标状态统计已选择项目数量
        Returns: 包含各状态统计数据的列表
        """
        sql = """
        WITH status_categories AS (
            SELECT 'not_started' as status UNION ALL
            SELECT 'in_progress' UNION ALL
            SELECT 'successful' UNION ALL
            SELECT 'failed' UNION ALL
            SELECT 'cancelled'
        ),
        time_periods AS (
            SELECT 
                CURRENT_DATE as today_start,
                DATE_TRUNC('week', CURRENT_DATE) as week_start,
                DATE_TRUNC('month', CURRENT_DATE) as month_start,
                DATE_TRUNC('year', CURRENT_DATE) as year_start
        )
        SELECT 
            sc.status,
            COUNT(*) FILTER (WHERE pp.created_at >= tp.today_start AND pp.is_selected = true) as today,
            COUNT(*) FILTER (WHERE pp.created_at >=tp.week_start AND pp.is_selected = true) as week,
            COUNT(*) FILTER (WHERE pp.created_at >= tp.month_start AND pp.is_selected = true) as month,
            COUNT(*) FILTER (WHERE pp.created_at >= tp.year_start AND pp.is_selected = true) as year,
            COUNT(*) FILTER (WHERE pp.is_selected = true) as total
        FROM status_categories sc
        CROSS JOIN time_periods tp
        LEFT JOIN procurement_purchasing pp ON sc.status = pp.bidding_status
        GROUP BY sc.status
        ORDER BY 
            CASE sc.status
                WHEN 'not_started' THEN 1
                WHEN 'in_progress' THEN 2
                WHEN 'successful' THEN 3
                WHEN 'failed' THEN 4
                WHEN 'cancelled' THEN 5
            END
        """
        
        with connection.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
            
            # 状态显示名称映射
            status_display_map = {
                'not_started': '未开始',
                'in_progress': '进行中',
                'successful': '成功',
                'failed': '失败',
                'cancelled': '已取消'
            }
            
            # 将结果映射到字典列表
            columns = ['status', 'today', 'week', 'month', 'year', 'total']
            result = []
            for row in rows:
                row_dict = dict(zip(columns, row))
                row_dict['status_display'] = status_display_map.get(row_dict['status'], row_dict['status'])
                result.append(row_dict)
            
            return result
