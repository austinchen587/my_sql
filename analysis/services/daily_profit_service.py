from django.db import connection

class DailyProfitService:
    """每日利润统计服务"""
    
    @staticmethod
    def get_daily_profit_stats():
        """获取每日利润统计数据"""
        sql = """
        SELECT 
            pe.project_name,
            pp.project_owner,
            -- 金额转换逻辑实现
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
            END as total_price_control,
            -- 供应商名称：优先显示选中的供应商，否则显示第一个供应商，没有则提示"询价中"
            COALESCE(
                MAX(CASE WHEN psr.is_selected = true THEN ps.name END),
                MAX(ps.name),
                '询价中'
            ) as supplier_name,
            -- 总报价：优先计算选中供应商的，否则计算第一个供应商的
            COALESCE(
                MAX(CASE WHEN psr.is_selected = true THEN (
                    SELECT SUM(sc.price * sc.quantity)
                    FROM supplier_commodities sc
                    WHERE sc.supplier_id = ps.id
                ) END),
                MAX((
                    SELECT SUM(sc.price * sc.quantity)
                    FROM supplier_commodities sc
                    WHERE sc.supplier_id = ps.id
                )),
                0
            ) as total_quote,
            -- 利润计算：total_price_control - total_quote
            (CASE 
                WHEN pe.total_price_control IS NULL OR pe.total_price_control = '-' THEN 0
                WHEN pe.total_price_control LIKE '%万元%' AND pe.total_price_control NOT LIKE '%元万元%' THEN 
                    CAST(REGEXP_REPLACE(pe.total_price_control, '[^0-9.]', '', 'g') AS NUMERIC) * 10000
                WHEN pe.total_price_control LIKE '%元万元%' THEN 
                    CAST(REGEXP_REPLACE(pe.total_price_control, '[^0-9.]', '', 'g') AS NUMERIC)
                WHEN pe.total_price_control LIKE '%元%' AND pe.total_price_control NOT LIKE '%万元%' THEN 
                    CAST(REGEXP_REPLACE(pe.total_price_control, '[^0-9.]', '', 'g') AS NUMERIC)
                ELSE 
                    COALESCE(CAST(REGEXP_REPLACE(pe.total_price_control, '[^0-9.]', '', 'g') AS NUMERIC), 0)
            END) - 
            COALESCE(
                MAX(CASE WHEN psr.is_selected = true THEN (
                    SELECT SUM(sc.price * sc.quantity)
                    FROM supplier_commodities sc
                    WHERE sc.supplier_id = ps.id
                ) END),
                MAX((
                    SELECT SUM(sc.price * sc.quantity)
                    FROM supplier_commodities sc
                    WHERE sc.supplier_id = ps.id
                )),
                0
            ) as profit,
            -- 最新备注
            (
                SELECT pr.remark_content 
                FROM procurement_purchasing_remarks pr 
                WHERE pr.purchasing_id = pp.id 
                ORDER BY pr.created_at DESC 
                LIMIT 1
            ) as latest_remark
        FROM procurement_emall pe
        -- 内连接：只获取当天发布且采购项目被选中的记录
        INNER JOIN procurement_purchasing pp ON pe.id = pp.procurement_id AND pp.is_selected = true
        -- 左连接：关联供应商（可能没有供应商）
        LEFT JOIN procurement_supplier_relation psr ON pp.id = psr.procurement_id
        LEFT JOIN procurement_suppliers ps ON psr.supplier_id = ps.id
        WHERE 
            -- 第一个条件：当天发布，匹配格式 "2025.12.03"
            pe.publish_date = TO_CHAR(CURRENT_DATE, 'YYYY.MM.DD')
        GROUP BY 
            pe.project_name, 
            pp.project_owner,
            pe.total_price_control,
            pp.id
        ORDER BY 
            pe.project_name;
        """
        
        with connection.cursor() as cursor:
            cursor.execute(sql)
            columns = [col[0] for col in cursor.description]
            results = [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]
        
        return results
