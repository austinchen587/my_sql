from django.db import connection
from django.utils import timezone
from datetime import timedelta
from typing import Dict, Any, List

class StatusStatsOwnerService:
    """按归属人竞标状态统计数据服务类"""
    
    @staticmethod
    def get_procurement_status_stats_by_owner(owner_name: str) -> List[Dict[str, Any]]:
        """
        按时间维度和竞标状态统计指定归属人的已选择项目数量
        """
        # [核心修复] 在 Python 层获取准确的本地（北京）时间边界
        now = timezone.localtime()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=now.weekday())
        month_start = today_start.replace(day=1)
        year_start = today_start.replace(month=1, day=1)

        sql = """
        WITH status_categories AS (
            SELECT 'not_started' as status UNION ALL
            SELECT 'in_progress' UNION ALL
            SELECT 'successful' UNION ALL
            SELECT 'failed' UNION ALL
            SELECT 'cancelled'
        )
        SELECT 
            sc.status,
            COUNT(*) FILTER (WHERE pp.created_at >= %s AND pp.is_selected = true AND pp.project_owner = %s) as today,
            COUNT(*) FILTER (WHERE pp.created_at >= %s AND pp.is_selected = true AND pp.project_owner = %s) as week,
            COUNT(*) FILTER (WHERE pp.created_at >= %s AND pp.is_selected = true AND pp.project_owner = %s) as month,
            COUNT(*) FILTER (WHERE pp.created_at >= %s AND pp.is_selected = true AND pp.project_owner = %s) as year,
            COUNT(*) FILTER (WHERE pp.is_selected = true AND pp.project_owner = %s) as total
        FROM status_categories sc
        LEFT JOIN procurement_purchasing pp ON 
            sc.status = pp.bidding_status 
            AND pp.project_owner = %s
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
            # 严格按照 SQL 中的参数顺序传入：时间, 归属人, 时间, 归属人... 最后是总数和 JOIN 的归属人
            params = [
                today_start, owner_name,
                week_start, owner_name,
                month_start, owner_name,
                year_start, owner_name,
                owner_name,
                owner_name
            ]
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            status_display_map = {
                'not_started': '未开始',
                'in_progress': '进行中',
                'successful': '成功',
                'failed': '失败',
                'cancelled': '已取消'
            }
            
            columns = ['status', 'today', 'week', 'month', 'year', 'total']
            result = []
            for row in rows:
                row_dict = dict(zip(columns, row))
                row_dict['status_display'] = status_display_map.get(row_dict['status'], row_dict['status'])
                result.append(row_dict)
            
            return result