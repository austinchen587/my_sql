# analysis/services/monthly_profit_service.py
from django.db import connection

class MonthlyProfitService:
    """月度利润汇总服务"""
    
    @staticmethod
    def get_monthly_profit_summary():
        """获取月度利润汇总数据"""
        sql = """
        WITH project_stats AS (
            SELECT 
                pe.project_title AS project_name,
                pe.quote_start_time AS start_time,
                ht.response_total AS response_total,
                (SELECT SUM(sc.payment_amount) 
                 FROM procurement_supplier_relation psr
                 JOIN supplier_commodities sc ON psr.supplier_id = sc.supplier_id
                 WHERE psr.procurement_id = pp.id AND psr.is_selected = true) AS purchase_payment_amount,
                pp.settlement_amount AS settlement_amount,
                DATE_PART('day', pp.winning_date::timestamp - pe.quote_start_time::timestamp) AS bid_cycle_days,
                DATE_PART('day', pp.settlement_date::timestamp - pp.winning_date::timestamp) AS settlement_cycle_days,
                TO_CHAR(pe.quote_start_time::timestamp, 'YYYY-MM') AS statistics_month
            FROM procurement_purchasing pp
            JOIN procurement_emall pe ON pp.procurement_id = pe.id
            LEFT JOIN ht_emall ht ON pe.project_number = ht.project_id
            WHERE pp.bidding_status = 'successful'
        ),
        monthly_summary AS (
            SELECT 
                statistics_month,
                COUNT(*) AS project_count,
                SUM(response_total) AS total_response_amount,
                SUM(purchase_payment_amount) AS total_purchase_amount,
                SUM(COALESCE(response_total, 0) - COALESCE(purchase_payment_amount, 0)) AS total_profit,
                CASE 
                    WHEN SUM(purchase_payment_amount) = 0 THEN 0
                    ELSE ROUND(((SUM(response_total) / SUM(purchase_payment_amount)) - 1)::numeric, 4)
                END AS total_profit_margin,
                CASE 
                    WHEN SUM(response_total) = 0 THEN 0
                    ELSE ROUND((SUM(settlement_amount) / SUM(response_total))::numeric, 4)
                END AS settlement_fund_rate,
                ROUND(AVG(bid_cycle_days)::numeric, 2) AS avg_bid_cycle,
                ROUND(AVG(settlement_cycle_days)::numeric, 2) AS avg_settlement_cycle
            FROM project_stats
 GROUP BY statistics_month
        )
        SELECT * FROM monthly_summary
        ORDER BY statistics_month DESC;
        """
        
        with connection.cursor() as cursor:
            cursor.execute(sql)
            columns = [col[0] for col in cursor.description]
            results = [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]
        
        return results
