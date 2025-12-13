from django.db import connection
from django.utils import timezone

class HtEmallReverseService:
    """
    HT电商平台反拍（Reverse Auction）数据服务
    提供反拍项目相关的查询与统计功能
    """

    @staticmethod
    def get_ht_emall_reverse_records():
        """
        获取 HT 电商平台反拍项目的全部记录（仅限交易类型为'反拍'）
        并按状态、时间排序
        """
        sql = """
        SELECT
          detail_status AS status_category,
          project_id,
          project_name,
          expected_total_price,
          response_total,
          bid_start_time,
          bid_end_time
        FROM ht_emall
        WHERE transaction_type = '反拍'
        ORDER BY
          status_category ASC NULLS LAST,
          bid_start_time DESC,
          project_id;
        """
        with connection.cursor() as cursor:
            cursor.execute(sql)
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return results
