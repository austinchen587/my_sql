# analysis/services/daily_profit_service.py
from django.db import connection
from django.utils import timezone

class DailyProfitService:
    """每日利润统计服务"""
    
    @staticmethod
    def get_daily_profit_stats():
        """获取每日利润统计数据（包含最终报价和选中时间）- 剔除selected_at为null的数据"""
        sql = """
        SELECT 
    pe.project_name,
    pp.project_owner,
    -- 金额转换逻辑保持不变
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
    -- 供应商名称
    COALESCE(
        STRING_AGG(
            CASE WHEN psr.is_selected = true THEN ps.name ELSE NULL END, 
            ', '
        ),
        '询价中'
    ) as supplier_name,
    -- 供应商创建人
    COALESCE(
        STRING_AGG(
            CASE WHEN psr.is_selected = true THEN ps.purchaser_created_by ELSE NULL END, 
            ', '
        ),
        '未知'
    ) as supplier_created_by,
    -- 供应商更新人
    COALESCE(
        STRING_AGG(
            CASE WHEN psr.is_selected = true THEN ps.purchaser_updated_by ELSE NULL END, 
            ', '
        ),
        '未知'
    ) as supplier_updated_by,
    --总报价
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
    -- 最终协商报价
    COALESCE(
        MAX(
            CASE WHEN psr.is_selected = true THEN psr.final_negotiated_quote ELSE NULL END
        ),
        0
    ) as final_negotiated_quote,
    -- 最新备注
    (
        SELECT pr.remark_content 
        FROM procurement_purchasing_remarks pr 
        WHERE pr.purchasing_id = pp.id 
        ORDER BY pr.created_at DESC 
        LIMIT 1
    ) as latest_remark,
    -- 选中时间
    pp.selected_at as selected_at,
    -- 是否选中
    pp.is_selected as is_selected
FROM procurement_emall pe
INNER JOIN procurement_purchasing pp ON pe.id = pp.procurement_id AND pp.is_selected = true
LEFT JOIN procurement_supplier_relation psr ON pp.id = psr.procurement_id
LEFT JOIN procurement_suppliers ps ON psr.supplier_id = ps.id
WHERE pp.selected_at IS NOT NULL  -- 新增：剔除selected_at为null的数据
GROUP BY 
    pe.project_name, 
    pp.project_owner,
    pe.total_price_control,
    pp.id,
    pp.selected_at,
    pp.is_selected
ORDER BY 
    pp.selected_at DESC,
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
