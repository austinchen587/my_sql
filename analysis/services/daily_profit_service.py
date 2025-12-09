# analysis/services/daily_profit_service.py
from django.db import connection
from django.utils import timezone

class DailyProfitService:
    """每日利润统计服务"""
    
    @staticmethod
    def get_daily_profit_stats():
        """获取每日利润统计数据（包含最终报价）"""
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
            -- 供应商名称：显示所有被选中供应商的名称，用逗号分隔
            COALESCE(
                STRING_AGG(
                    CASE WHEN psr.is_selected = true THEN ps.name ELSE NULL END, 
                    ', '
                ),
                '询价中'
            ) as supplier_name,
            -- 总报价：计算所有被选中供应商的总报价
            COALESCE(
                SUM(
                    CASE WHEN psr.is_selected = true THEN (
                        SELECT SUM(sc.price * sc.quantity)
                        FROM supplier_commodities sc
                        WHERE sc.supplier_id = ps.id
                    ) ELSE 0 END
                ),
                0
            ) as total_quote,
            -- 最终协商报价：获取被选中供应商的最终报价
            COALESCE(
                MAX(
                    CASE WHEN psr.is_selected = true THEN psr.final_negotiated_quote ELSE NULL END
                ),
                0
            ) as final_negotiated_quote,
            -- 最终报价修改信息（用于调试）
            MAX(
                CASE WHEN psr.is_selected = true THEN psr.final_quote_modified_by ELSE NULL END
            ) as final_quote_modifier,
            MAX(
                CASE WHEN psr.is_selected = true THEN psr.final_quote_modified_at ELSE NULL END
            ) as final_quote_modified_at,
            -- 最新备注
            (
                SELECT pr.remark_content 
                FROM procurement_purchasing_remarks pr 
                WHERE pr.purchasing_id = pp.id 
                ORDER BY pr.created_at DESC 
                LIMIT 1
            ) as latest_remark
        FROM procurement_emall pe
        -- 内连接：只获取采购项目被选中的记录
        INNER JOIN procurement_purchasing pp ON pe.id = pp.procurement_id AND pp.is_selected = true
        -- 左连接：关联供应商（可能没有供应商）
        LEFT JOIN procurement_supplier_relation psr ON pp.id = psr.procurement_id
        LEFT JOIN procurement_suppliers ps ON psr.supplier_id = ps.id
        WHERE 
            -- 修改条件：使用selected_at字段筛选当天的记录
            pp.selected_at >= CURRENT_DATE 
            AND pp.selected_at < CURRENT_DATE + INTERVAL '1 day'
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
