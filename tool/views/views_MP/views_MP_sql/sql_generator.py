# tool/views/views_MP/views_MP_sql/sql_generator.py
import logging
import re
import traceback

logger = logging.getLogger(__name__)

class SQLGenerator:
    """SQL生成模块"""
    
    def __init__(self, ai_processor):
        self.ai_processor = ai_processor
    
    def generate_intelligent_sql(self, user_message, schema_understanding, session_id):
        """使用AI智能生成SQL查询"""
        try:
            if not self.ai_processor.ai_client:
                return self.error_response_dict("AI服务不可用，无法生成智能SQL")
            
            # 构建提示词，让AI基于schema理解生成SQL
            prompt = self.build_sql_generation_prompt(user_message, schema_understanding)
            
            logger.info("🤖 请求AI生成SQL查询...")
            
            response = self.ai_processor.ai_client.chat.completions.create(
                model=self.ai_processor.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.1
            )
            
            ai_content = response.choices[0].message.content
            logger.info(f"📝 AI原始响应: {ai_content[:200]}...")
            
            # 从AI响应中提取SQL语句
            sql_query = self.extract_sql_from_ai_response(ai_content)
            
            if not sql_query:
                logger.error("❌ AI未能生成有效的SQL语句")
                return self.error_response_dict("AI未能生成有效的SQL语句")
            
            # 验证SQL安全性
            if not self.validate_sql_safety(sql_query):
                logger.error(f"❌ SQL安全验证失败: {sql_query}")
                return self.error_response_dict("生成的SQL语句不符合安全要求")
            
            logger.info(f"✅ AI生成的SQL: {sql_query}")
            
            return {
                'status': 'success',
                'sql_query': sql_query,
                'ai_explanation': ai_content,
                'tables_used': self.extract_tables_from_sql(sql_query)
            }
            
        except Exception as e:
            logger.error(f"❌ AI生成SQL失败: {e}")
            return self.error_response_dict(f"AI生成SQL失败: {str(e)}")

    def build_sql_generation_prompt(self, user_message, schema_understanding):
        """构建SQL生成提示词"""
        schema_info = self.format_schema_for_ai(schema_understanding)
        
        prompt = f"""
您是一个PostgreSQL专家。请根据用户的问题和提供的数据库结构，生成准确且高效的SQL查询语句。
# 数据库结构信息：
{schema_info}
# 用户问题：
{user_message}
# 重要说明：
- `procurement_intention`表存储采购意向信息，包含预算金额字段`intention_budget_amount`
- `base_procurement_info_new`表包含基本信息如标题、发布时间等
- 教育相关的信息可能在`title`、`info_type`或`jurisdiction`字段中
- 11月的数据使用`EXTRACT(MONTH FROM publish_time) = 11`或`publish_time >= '2025-11-01'`筛选
# 生成要求：
1. 只使用SELECT查询，严禁INSERT/UPDATE/DELETE等操作
2. 使用LEFT JOIN关联表，通过url字段连接
3. 包含必要的WHERE条件匹配用户需求，但不要过于严格
4. 使用LIMIT限制结果数量（不超过100条）
5. 选择最相关的字段，避免SELECT *
# 请直接返回SQL查询语句，用```sql```包裹。
"""
        return prompt

    def format_schema_for_ai(self, schema_understanding):
        """格式化schema信息供AI理解"""
        tables_schema = schema_understanding.get('tables_schema', {})
        sample_data = schema_understanding.get('sample_data', {})
        relationships = schema_understanding.get('table_relationships', {})
        
        schema_text = "## 数据库表结构\n\n"
        
        for table_name, columns in tables_schema.items():
            schema_text += f"### 表: {table_name}\n"
            schema_text += "| 字段名 | 数据类型 | 可空 | 默认值 |\n"
            schema_text += "|--------|----------|------|--------|\n"
            
            for col in columns:
                schema_text += f"| {col['column_name']} | {col['data_type']} | {col['is_nullable']} | {col['column_default'] or 'NULL'} |\n"
            
            # 添加样本数据
            if table_name in sample_data:
                sample = sample_data[table_name]
                schema_text += f"\n**样本数据:**\n"
                schema_text += f"```json\n{sample['sample_row']}\n```\n"
            
            schema_text += "\n"
        
        # 添加表关系
        schema_text += "## 表关系\n"
        for rel in relationships.get('relationships', []):
            schema_text += f"- {rel['table1']} ↔ {rel['table2']} (关联字段: {rel['join_key']})\n"
        
        return schema_text

    def extract_sql_from_ai_response(self, ai_content):
        """从AI响应中提取SQL语句"""
        # 尝试从代码块中提取SQL
        sql_match = re.search(r'```sql\n(.*?)\n```', ai_content, re.DOTALL)
        if sql_match:
            return sql_match.group(1).strip()
        
        # 如果没有代码块，尝试直接提取SELECT语句
        select_match = re.search(r'(SELECT.*?)(?=;|$)', ai_content, re.DOTALL | re.IGNORECASE)
        if select_match:
            return select_match.group(1).strip()
        
        return None

    def validate_sql_safety(self, sql_query):
        """验证SQL安全性"""
        sql_upper = sql_query.upper().strip()
        forbidden_keywords = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE', 'TRUNCATE']
        
        if not sql_upper.startswith('SELECT'):
            return False
        
        for keyword in forbidden_keywords:
            if keyword in sql_upper:
                return False
        
        return True

    def extract_tables_from_sql(self, sql_query):
        """从SQL中提取使用的表"""
        tables = re.findall(r'FROM\s+(\w+)', sql_query, re.IGNORECASE)
        tables.extend(re.findall(r'JOIN\s+(\w+)', sql_query, re.IGNORECASE))
        return list(set(tables))

    def error_response_dict(self, message):
        """错误响应"""
        return {
            'status': 'error',
            'message': f'<div class="alert alert-danger">{message}</div>'
        }
