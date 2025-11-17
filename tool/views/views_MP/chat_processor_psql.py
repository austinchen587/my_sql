# tool/views/views_MP/chat_processor_psql.py
import logging
import re
import traceback
from django.db import connection

logger = logging.getLogger(__name__)

class PSQLDataProcessor:
    """PSQL数据处理器 - 协调各个模块工作"""
    
    def __init__(self, ai_processor):
        self.ai_processor = ai_processor
        # 初始化各个模块
        from .views_MP_sql.schema_manager import SchemaManager
        from .views_MP_sql.sql_generator import SQLGenerator
        from .views_MP_sql.query_executor import QueryExecutor
        from .views_MP_sql.result_analyzer import ResultAnalyzer
        from .views_MP_sql.response_formatter import ResponseFormatter
        
        self.schema_manager = SchemaManager()
        self.sql_generator = SQLGenerator(ai_processor)
        self.query_executor = QueryExecutor()
        self.result_analyzer = ResultAnalyzer(ai_processor)
        self.response_formatter = ResponseFormatter()
    
    def clean_psql_marker(self, message):
        """清理消息中的 psql 标记"""
        cleaned = re.sub(r'#psql|#p\s*s\s*q\s*l|#psq\b', '', message, flags=re.IGNORECASE).strip()
        return cleaned
    
    def check_if_psql_analysis_needed(self, message):
        """检查是否需要PSQL数据分析"""
        psql_patterns = [
            r'#psql\b',
            r'#p\s*s\s*q\s*l\b', 
            r'#psq\b',
            r'数据分析|数据查询|查询数据|统计信息'
        ]
        
        clean_msg = message.lower().strip()
        
        for pattern in psql_patterns:
            if re.search(pattern, clean_msg, re.IGNORECASE):
                return True
        
        return False
    
    def handle_intelligent_data_analysis(self, user_message, session_id, user_sessions):
        """智能数据分析处理 - 主流程控制"""
        try:
            clean_message = self.clean_psql_marker(user_message)
            logger.info(f"🔍 开始智能数据分析: {clean_message}")
            
            # 第一步：让大模型理解数据库结构（Schema + 样本数据）
            schema_understanding = self.schema_manager.help_ai_understand_schema()
            logger.info("✅ 数据库结构理解完成")
            
            # 第二步：智能分析用户问题并生成SQL
            sql_generation_result = self.sql_generator.generate_intelligent_sql(
                clean_message, schema_understanding, session_id
            )
            
            if sql_generation_result['status'] == 'error':
                return sql_generation_result
            
            logger.info("✅ SQL生成完成")
            
            # 第三步：执行SQL并获取结果
            query_result = self.query_executor.execute_sql_query(sql_generation_result['sql_query'])
            
            if query_result is None:
                return self.error_response_dict("数据库查询失败")
            
            logger.info(f"✅ 查询执行完成，获取 {len(query_result)} 条记录")
            
            # 第四步：使用AI分析查询结果
            analysis_result = self.result_analyzer.analyze_query_results_with_ai(
                clean_message, query_result, sql_generation_result['sql_query']
            )
            
            logger.info("✅ AI结果分析完成")
            
            # 第五步：格式化最终响应（显示SQL + 结果 + 分析）
            final_response = self.response_formatter.format_final_response(
                clean_message, sql_generation_result, query_result, analysis_result
            )
            
            logger.info(f"🎉 智能分析流程完成")
            return final_response
            
        except Exception as e:
            logger.error(f"❌ 智能数据分析处理失败: {e}")
            logger.error(traceback.format_exc())
            return self.error_response_dict(f"分析失败: {str(e)}")
    
    def check_if_needs_database_intro(self, message, session_id):
        """检查是否需要数据库介绍"""
        intro_keywords = ['数据库', '表结构', 'schema', '表有哪些', '数据结构', '字段', '表名', '列名']
        clean_msg = self.clean_psql_marker(message).lower()
        
        for keyword in intro_keywords:
            if keyword in clean_msg:
                logger.info(f"🔍 检测到需要数据库介绍的关键词: {keyword}")
                return True
        
        simple_questions = ['介绍', '说明', '帮助', '有哪些表', '什么数据']
        for question in simple_questions:
            if question in clean_msg and len(clean_msg) < 20:
                logger.info(f"🔍 检测到简单问题，需要数据库介绍")
                return True
                
        return False
    
    def handle_database_introduction(self, message, session_id):
        """处理数据库介绍请求"""
        try:
            schema_understanding = self.schema_manager.help_ai_understand_schema()
            
            tables_info = ""
            for table_name, columns in schema_understanding.get('tables_schema', {}).items():
                tables_info += f"\n### {table_name}表\n"
                tables_info += "主要字段："
                key_fields = []
                for col in columns[:8]:
                    key_fields.append(col['column_name'])
                tables_info += ", ".join(key_fields)
                if len(columns) > 8:
                    tables_info += f" 等{len(columns)}个字段"
            
            relationships = schema_understanding.get('table_relationships', {})
            relations_info = "\n\n### 表关系\n"
            for rel in relationships.get('relationships', []):
                relations_info += f"- {rel['table1']} ↔ {rel['table2']} (通过{rel['join_key']}关联)\n"
            
            introduction = f"""
    ## 📊 数据库结构介绍
    本系统包含以下数据表：{tables_info}
    {relations_info}
    ### 💡 使用提示
    - 您可以通过自然语言提问查询数据
    - 系统会自动生成SQL查询并返回结果
    - 支持按时间、地区、行业等条件筛选
    请告诉我您想查询什么信息？
            """.strip()
            
            return {
                'status': 'success',
                'response_type': 'database_intro',
                'message': f'<div class="database-intro">{introduction}</div>',
                'data_count': 0
            }
            
        except Exception as e:
            logger.error(f"❌ 数据库介绍处理失败: {e}")
            return self.error_response_dict("数据库介绍生成失败")

    def error_response_dict(self, message):
        """错误响应"""
        return {
            'status': 'error',
            'message': f'<div class="alert alert-danger">{message}</div>'
        }
