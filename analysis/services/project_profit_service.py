# analysis/services/project_profit_service.py
from django.db import connection
from django.utils import timezone

class ProjectProfitService:
    """项目利润统计服务"""
    
    @staticmethod
    def get_project_profit_stats():
        """获取项目利润统计数据"""
        sql = """
        WITH project_stats AS (
            SELECT 
                pe.project_title AS project_name,
                pe.quote_start_time AS start_time,
                pe.quote_end_time AS end_time,
                '竞标成功' AS project_status,
                pp.project_owner AS project_owner,
                CASE 
                    WHEN pe.total_price_control IS NULL OR pe.total_price_control = '-' THEN 0
                    WHEN pe.total_price_control LIKE '%万元%' AND pe.total_price_control NOT LIKE '%元万元%' THEN 
                        CAST(REGEXP_REPLACE(pe.total_price_control, '[^0-9.]', '', 'g') AS NUMERIC) * 10000
                    WHEN pe.total_price_control LIKE '%元万元%' THEN 
                        CAST(REGEXP_REPLACE(pe.total_price_control, '[^0-9.]', '', 'g') AS NUMERIC)
                    WHEN pe.total_price_control LIKE '%元%' AND pe.total_price_control NOT LIKE '%万元%' THEN 
                        CAST(REGEXP_REPLACE(pe.total_price_control, '[^0-9.]', '', 'g') AS NUMERIC)
                    ELSE 
                        COALESCE(CAST(REGEXP_REPLACE(pe.total_price_control, '[^0-9.]', '', 'g') AS NUMERIC), 0)
                END AS expected_total_price,
                ht.response_total AS response_total,
                pp.winning_date AS winning_date,
                pp.settlement_amount AS settlement_amount,
                pp.settlement_date AS settlement_date,
                (SELECT psr.final_negotiated_quote 
                 FROM procurement_supplier_relation psr
                 WHERE psr.procurement_id = pp.id AND psr.is_selected = true
                 LIMIT 1) AS final_quote,
                (SELECT SUM(sc.payment_amount) 
                 FROM procurement_supplier_relation psr
                 JOIN supplier_commodities sc ON psr.supplier_id = sc.supplier_id
                 WHERE psr.procurement_id = pp.id AND psr.is_selected = true) AS purchase_payment_amount,
                pp.id AS procurement_id,
                pe.project_number AS project_number,
                DATE_PART('day', pp.winning_date::timestamp - pe.quote_start_time::timestamp) AS bid_cycle_days,
                DATE_PART('day', pp.settlement_date::timestamp - pp.winning_date::timestamp) AS settlement_cycle_days,
                COALESCE(ht.response_total, 0) - 
                COALESCE((SELECT SUM(sc.payment_amount) 
                 FROM procurement_supplier_relation psr
                 JOIN supplier_commodities sc ON psr.supplier_id = sc.supplier_id
                 WHERE psr.procurement_id = pp.id AND psr.is_selected = true), 0) AS project_profit,
                CASE 
                    WHEN COALESCE((SELECT SUM(sc.payment_amount) 
                          FROM procurement_supplier_relation psr
                          JOIN supplier_commodities sc ON psr.supplier_id = sc.supplier_id
                          WHERE psr.procurement_id = pp.id AND psr.is_selected = true), 0) = 0 THEN 0
                    ELSE ROUND(
                        ((COALESCE(ht.response_total, 0) / 
                         COALESCE((SELECT SUM(sc.payment_amount) 
                          FROM procurement_supplier_relation psr
                          JOIN supplier_commodities sc ON psr.supplier_id = sc.supplier_id
                          WHERE psr.procurement_id = pp.id AND psr.is_selected = true), 1)) - 1)::numeric, 4)
                END AS project_profit_margin,
                TO_CHAR(pe.quote_start_time::timestamp, 'YYYY-MM') AS statistics_month
            FROM procurement_purchasing pp
            JOIN procurement_emall pe ON pp.procurement_id = pe.id
            LEFT JOIN ht_emall ht ON pe.project_number = ht.project_id
            WHERE pp.bidding_status = 'successful'
        )
        SELECT * FROM project_stats
        ORDER BY start_time DESC;
        """
        
        with connection.cursor() as cursor:
            cursor.execute(sql)
            columns = [col[0] for col in cursor.description]
            results = []
            for row in cursor.fetchall():
                row_dict = dict(zip(columns, row))
                # 确保日期时间字段是字符串格式
                for date_field in ['start_time', 'end_time', 'winning_date', 'settlement_date']:
                    if row_dict.get(date_field) and hasattr(row_dict[date_field], 'strftime'):
                        row_dict[date_field] = row_dict[date_field].strftime('%Y-%m-%d %H:%M:%S')
                results.append(row_dict)
        
        return results
