# analysis/services/ht_emall_service.py
from django.db import connection
from django.utils import timezone

class HtEmallService:
    """
    HT电商平台竞价数据服务
    提供竞价项目相关的查询与统计功能
    """

    @staticmethod
    def get_ht_emall_records():
        """
        获取 HT 电商平台竞价项目的全部记录（仅限交易类型为'竞价'）
        并按状态、时间排序
        """
        sql = """
        SELECT
          ht.detail_status AS status_category,
          ht.project_id,
          pe.id AS procurement_emall_id,
          pe.project_name AS procurement_project_name,
          ht.expected_total_price,
          ht.response_total,
          ht.bid_start_time,
          ht.bid_end_time
        FROM ht_emall ht
        LEFT JOIN procurement_emall pe
          ON ht.project_id = pe.project_number
        WHERE ht.transaction_type = '竞价'
        ORDER BY
          status_category ASC NULLS LAST,
          ht.bid_start_time DESC,
          ht.project_id;
        """
        with connection.cursor() as cursor:
            cursor.execute(sql)
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return results

    # ...existing code...
