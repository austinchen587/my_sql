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
        获取 HT 电商平台反拍项目的全部记录（仅限交易类型为'反拍'且region包含'-反拍'）
        并按状态、时间排序
        """
        sql = """
        SELECT
            ht.detail_status AS status_category,
            ht.project_id,
            pe.project_name,
            ht.expected_total_price,
            ht.response_total,
            ht.bid_start_time,
            ht.bid_end_time,
            pe.region,
            pp.project_owner,
            pp.winning_date,
            pp.settlement_date,
            pp.settlement_amount,
            CASE 
                WHEN pp.bidding_status = 'not_started' THEN '未开始'
                WHEN pp.bidding_status = 'in_progress' THEN '进行中'
                WHEN pp.bidding_status = 'successful' THEN '竞标成功'
                WHEN pp.bidding_status = 'failed' THEN '竞标失败'
                WHEN pp.bidding_status = 'cancelled' THEN '已取消'
                ELSE pp.bidding_status
            END AS bidding_status
        FROM ht_emall ht
        LEFT JOIN procurement_emall pe
            ON ht.project_id = pe.project_number
        LEFT JOIN procurement_purchasing pp
            ON pe.id = pp.procurement_id
        WHERE ht.transaction_type = '反拍'
            AND pe.region LIKE '%-反拍'
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
