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
          CASE 
            WHEN pp.bidding_status = 'not_started' THEN '未开始'
            WHEN pp.bidding_status = 'in_progress' THEN '进行中'
            WHEN pp.bidding_status = 'successful' THEN '竞标成功'
            WHEN pp.bidding_status = 'failed' THEN '竞标失败'
            WHEN pp.bidding_status = 'cancelled' THEN '已取消'
            ELSE pp.bidding_status
          END AS bidding_status,  -- 直接替换为映射后的中文状态
          pe.id AS procurement_emall_id,
          pe.project_name AS procurement_project_name,
          ht.expected_total_price,
          ht.response_total,
          ht.bid_start_time,
          ht.bid_end_time,
          pp.project_owner,  -- 新增项目归属人字段
          pp.winning_date,  -- 中标日期
          pp.settlement_date,  -- 结算日期
          pp.settlement_amount  -- 结算金额
        FROM ht_emall ht
        LEFT JOIN procurement_emall pe
          ON ht.project_id = pe.project_number
        LEFT JOIN procurement_purchasing pp
          ON pe.id = pp.procurement_id
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
