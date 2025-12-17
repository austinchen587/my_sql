# fp_emall/services/fp_emall_list_service.py
from django.db import connection

class FpEmallListService:
    """FP Emall 列表数据服务"""
    
    @staticmethod
    def get_fp_emall_list(page=1, page_size=100):
        """获取FP Emall列表数据"""
        offset = (page - 1) * page_size
        
        # 先创建函数（只在第一次需要）
        create_function_sql = """
        CREATE OR REPLACE FUNCTION convert_price_format(price_text TEXT)
        RETURNS NUMERIC AS $$
        DECLARE
            number_value NUMERIC;
        BEGIN
            -- 1. 先检查"万元"（不包含"元万元"的情况）
            IF price_text LIKE '%万元%' AND price_text NOT LIKE '%元万元%' THEN
                number_value := substring(price_text from '(\\d+\\.?\\d*)万元')::NUMERIC;
                IF number_value IS NOT NULL THEN
                    RETURN number_value * 10000;
                END IF;
            END IF;
            
            -- 2. 处理"元万元"情况（直接提取数字，不乘以10000）
            IF price_text LIKE '%元万元%' THEN
                number_value := substring(price_text from '(\\d+\\.?\\d*)')::NUMERIC;
                IF number_value IS NOT NULL THEN
                    RETURN number_value;
                END IF;
            END IF;
            
            -- 3. 处理单独的"元"情况
            IF price_text LIKE '%元%' AND price_text NOT LIKE '%万元%' THEN
                number_value := substring(price_text from '(\\d+\\.?\\d*)元')::NUMERIC;
                IF number_value IS NOT NULL THEN
                    RETURN number_value;
                END IF;
            END IF;
            
            -- 4. 如果没有匹配的模式，尝试直接提取数字
            number_value := substring(price_text from '(\\d+\\.?\\d*)')::NUMERIC;
            RETURN number_value;
        END;
        $$ LANGUAGE plpgsql;
        """
        
        # 查询语句
        select_sql = """
        SELECT 
            fp_project_name,
            fp_project_number,
            fp_purchasing_unit,
            fp_total_price_control,
            convert_price_format(fp_total_price_control) AS converted_price,
            fp_quote_start_time,
            fp_quote_end_time
        FROM procurement_fp_emall
        WHERE fp_total_price_control IS NOT NULL
        ORDER BY converted_price DESC
        LIMIT %s OFFSET %s
        """
        
        with connection.cursor() as cursor:
            # 先创建函数
            try:
                cursor.execute(create_function_sql)
            except Exception:
                # 如果函数已存在，忽略错误
                pass
            
            # 再执行查询
            cursor.execute(select_sql, [page_size, offset])
            columns = [col[0] for col in cursor.description]
            results = [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]
        
        return results
    
    @staticmethod
    def get_total_count():
        """获取总记录数"""
        sql = "SELECT COUNT(*) FROM procurement_fp_emall WHERE fp_total_price_control IS NOT NULL"
        
        with connection.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchone()[0]
