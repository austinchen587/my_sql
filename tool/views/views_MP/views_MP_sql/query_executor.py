# tool/views/views_MP/views_MP_sql/query_executor.py
import logging
import traceback
import json
from django.db import connection

logger = logging.getLogger(__name__)

class QueryExecutor:
    """SQL执行模块"""
    
    def execute_sql_query(self, sql_query):
        """执行SQL查询"""
        try:
            logger.info(f"🔍 执行SQL查询: {sql_query[:200]}...")
            
            with connection.cursor() as cursor:
                # 安全检查
                sql_upper = sql_query.upper().strip()
                if not sql_upper.startswith('SELECT'):
                    logger.warning(f"⚠️ 非SELECT查询被拒绝: {sql_query}")
                    return None
                
                cursor.execute(sql_query)
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                
                logger.info(f"✅ SQL查询成功，返回 {len(rows)} 条记录")
                
                # 转换结果
                result = []
                for row in rows:
                    row_dict = {}
                    for i, col in enumerate(columns):
                        value = row[i]
                        # 处理JSON字段
                        if value and isinstance(value, str) and value.strip().startswith('{'):
                            try:
                                row_dict[col] = json.loads(value)
                            except:
                                row_dict[col] = value
                        else:
                            row_dict[col] = value
                    result.append(row_dict)
                
                return result
        except Exception as e:
            logger.error(f"❌ SQL执行失败: {e}")
            logger.error(traceback.format_exc())
            return None
