# fp_emall/services/fp_emall_search_service.py
from django.db import connection

class FpEmallSearchService:
    """FP Emall 搜索服务"""
    
    @staticmethod
    def search_fp_emall(page=1, page_size=100, search='', search_field=''):
        """根据搜索条件获取FP Emall列表数据"""
        offset = (page - 1) * page_size
        
        # 基础查询
        base_sql = """
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
        """
        
        # 添加搜索条件
        conditions = []
        params = []
        
        print(f"DEBUG Service - search: '{search}', search_field: '{search_field}'")  # 调试信息
        
        if search and search_field:
            # 确保search_field是有效的字段名
            valid_fields = ['fp_project_name', 'fp_project_number', 'fp_purchasing_unit', 'converted_price']
            
            if search_field in valid_fields:
                if search_field == 'converted_price':
                    try:
                        # 价格字段精确匹配
                        price_value = float(search)
                        conditions.append("convert_price_format(fp_total_price_control) = %s")
                        params.append(price_value)
                    except ValueError:
                        # 如果转换失败，使用文本模糊匹配
                        conditions.append("convert_price_format(fp_total_price_control)::text ILIKE %s")
                        params.append(f'%{search}%')
                else:
                    # 其他字段模糊搜索
                    conditions.append(f"{search_field} ILIKE %s")
                    params.append(f'%{search}%')
        
        # 组合查询条件
        if conditions:
            base_sql += " AND " + " AND ".join(conditions)
            print(f"DEBUG Service - 应用搜索条件: {conditions}, 参数: {params}")  # 调试信息
        
        # 添加排序和分页
        base_sql += " ORDER BY converted_price DESC LIMIT %s OFFSET %s"
        params.extend([page_size, offset])
        
        print(f"DEBUG Service - 最终SQL: {base_sql}")  # 调试信息
        print(f"DEBUG Service - 所有参数: {params}")  # 调试信息
        
        with connection.cursor() as cursor:
            cursor.execute(base_sql, params)
            columns = [col[0] for col in cursor.description]
            results = [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]
        
        print(f"DEBUG Service - 返回结果数量: {len(results)}")  # 调试信息
        return results
    
    @staticmethod
    def get_search_count(search='', search_field=''):
        """根据搜索条件获取总记录数"""
        sql = "SELECT COUNT(*) FROM procurement_fp_emall WHERE fp_total_price_control IS NOT NULL"
        
        conditions = []
        params = []
        
        if search and search_field:
            valid_fields = ['fp_project_name', 'fp_project_number', 'fp_purchasing_unit', 'converted_price']
            
            if search_field in valid_fields:
                if search_field == 'converted_price':
                    try:
                        price_value = float(search)
                        conditions.append("convert_price_format(fp_total_price_control) = %s")
                        params.append(price_value)
                    except ValueError:
                        conditions.append("convert_price_format(fp_total_price_control)::text ILIKE %s")
                        params.append(f'%{search}%')
                else:
                    conditions.append(f"{search_field} ILIKE %s")
                    params.append(f'%{search}%')
        
        if conditions:
            sql += " AND " + " AND ".join(conditions)
        
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()[0]
    
    @staticmethod
    def get_search_fields():
        """返回可搜索的字段列表"""
        return [
            {'value': 'fp_project_name', 'label': '项目名称'},
            {'value': 'fp_project_number', 'label': '项目编号'},
            {'value': 'fp_purchasing_unit', 'label': '采购单位'},
            {'value': 'converted_price', 'label': '转换价格'}
        ]
