# tool/views/views_MP/chat_processor_psql.py
import logging
import re
import traceback
from django.db import connection
from decimal import Decimal

logger = logging.getLogger(__name__)

class PSQLDataProcessor:
    """PSQL数据处理器 - 重新设计的智能SQL生成流程"""
    
    def __init__(self, ai_processor):
        self.ai_processor = ai_processor
    
    def clean_psql_marker(self, message):
        """清理消息中的 psql 标记"""
        # 支持多种标记格式
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
        """智能数据分析处理 - 按照新逻辑重新设计"""
        try:
            clean_message = self.clean_psql_marker(user_message)
            logger.info(f"🔍 开始智能数据分析: {clean_message}")
            
            # 第一步：让大模型理解数据库结构（Schema + 样本数据）
            schema_understanding = self.help_ai_understand_schema()
            logger.info("✅ 数据库结构理解完成")
            
            # 第二步：智能分析用户问题并生成SQL
            sql_generation_result = self.generate_intelligent_sql(
                clean_message, schema_understanding, session_id
            )
            
            if sql_generation_result['status'] == 'error':
                return sql_generation_result
            
            logger.info("✅ SQL生成完成")
            
            # 第三步：执行SQL并获取结果
            query_result = self.execute_sql_query(sql_generation_result['sql_query'])
            
            if query_result is None:
                return self.error_response_dict("数据库查询失败")
            
            logger.info(f"✅ 查询执行完成，获取 {len(query_result)} 条记录")
            
            # 第四步：使用AI分析查询结果
            analysis_result = self.analyze_query_results_with_ai(
                clean_message, query_result, sql_generation_result['sql_query']
            )
            
            logger.info("✅ AI结果分析完成")
            
            # 第五步：格式化最终响应（显示SQL + 结果 + 分析）
            final_response = self.format_final_response(
                clean_message, sql_generation_result, query_result, analysis_result
            )
            
            logger.info(f"🎉 智能分析流程完成")
            return final_response
            
        except Exception as e:
            logger.error(f"❌ 智能数据分析处理失败: {e}")
            logger.error(traceback.format_exc())
            return self.error_response_dict(f"分析失败: {str(e)}")

    def help_ai_understand_schema(self):
        """帮助AI理解数据库表结构 - 提供3个表的schema和1条样本数据"""
        try:
            # 获取三个核心表的schema信息
            tables_schema = self.get_tables_schema()
            
            # 获取每个表的1条样本数据
            sample_data = self.get_sample_data_from_tables()
            
            understanding_data = {
                'tables_schema': tables_schema,
                'sample_data': sample_data,
                'table_relationships': self.get_table_relationships()
            }
            
            logger.info(f"📊 数据库理解数据准备完成: {len(tables_schema)}个表结构, {len(sample_data)}个样本")
            return understanding_data
            
        except Exception as e:
            logger.error(f"❌ 获取数据库schema失败: {e}")
            return {}

    def get_tables_schema(self):
        """获取三个核心表的schema信息"""
        try:
            schema_query = """
            SELECT 
                table_name, 
                column_name, 
                data_type, 
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_name IN ('base_procurement_info_new', 'procurement_notices', 'procurement_intention')
            ORDER BY table_name, ordinal_position
            """
            
            with connection.cursor() as cursor:
                cursor.execute(schema_query)
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                
                # 按表名组织schema信息
                tables_schema = {}
                for row in rows:
                    table_name = row[0]
                    if table_name not in tables_schema:
                        tables_schema[table_name] = []
                    
                    tables_schema[table_name].append({
                        'column_name': row[1],
                        'data_type': row[2],
                        'is_nullable': row[3],
                        'column_default': row[4]
                    })
                
                logger.info(f"📋 获取到表结构: {list(tables_schema.keys())}")
                return tables_schema
                
        except Exception as e:
            logger.error(f"❌ 获取表schema失败: {e}")
            return {}

    def get_sample_data_from_tables(self):
        """从每个表获取1条样本数据"""
        try:
            sample_data = {}
            
            tables = ['base_procurement_info_new', 'procurement_notices', 'procurement_intention']
            
            with connection.cursor() as cursor:
                for table in tables:
                    if table == 'procurement_notices':
                        # 显式指定需要的字段，排除content字段
                        sample_query = """
                        SELECT url, info_type, title, jurisdiction, bid_type, 
                            publish_time, crawl_time, created_time
                        FROM procurement_notices 
                        LIMIT 1
                        """
                    else:
                        sample_query = f"SELECT * FROM {table} LIMIT 1"
                    
                    cursor.execute(sample_query)
                    columns = [col[0] for col in cursor.description]
                    row = cursor.fetchone()
                    
                    if row:
                        # 处理JSON字段
                        row_data = {}
                        for i, col_name in enumerate(columns):
                            value = row[i]
                            # 特殊处理可能的JSON字段
                            if value and isinstance(value, str) and value.strip().startswith('{'):
                                try:
                                    import json
                                    row_data[col_name] = json.loads(value)
                                except:
                                    row_data[col_name] = value
                            else:
                                row_data[col_name] = value
                        
                        sample_data[table] = {
                            'columns': columns,
                            'sample_row': row_data
                        }
                        logger.info(f"📄 获取表 {table} 的样本数据，列数: {len(columns)}")
            
            return sample_data
            
        except Exception as e:
            logger.error(f"❌ 获取样本数据失败: {e}")
            return {}

    def get_table_relationships(self):
        """获取表之间的关系"""
        relationships = {
            'relationships': [
                {
                    'table1': 'base_procurement_info_new',
                    'table2': 'procurement_notices', 
                    'join_key': 'url',
                    'relationship': '一对一或一对多，通过url字段关联'
                },
                {
                    'table1': 'base_procurement_info_new',
                    'table2': 'procurement_intention',
                    'join_key': 'url', 
                    'relationship': '一对一或一对多，通过url字段关联'
                }
            ],
            'key_fields': {
                'base_procurement_info_new': ['url', 'title', 'jurisdiction', 'info_type', 'publish_time'],
                'procurement_notices': ['url', 'title', 'publish_time', 'procurement_method', 'budget_amount'],
                'procurement_intention': ['url', 'intention_budget_amount', 'intention_procurement_unit', 'intention_project_name']
            },
            'join_instructions': '所有表通过url字段进行LEFT JOIN关联，base_procurement_info_new是主表'
        }
        return relationships
    
    def remove_duplicate_messages(self, messages):
        """移除重复的消息，保留最新的一个"""
        if not messages:
            return []
        
        seen_content = set()
        unique_messages = []
        
        for message in reversed(messages):
            content = message.get('content', '')
            if content not in seen_content:
                seen_content.add(content)
                unique_messages.append(message)
        
        return list(reversed(unique_messages))

    

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
                                import json
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

    def analyze_query_results_with_ai(self, user_message, query_result, sql_query):
        """使用AI分析查询结果 - 增加超时处理"""
        try:
            if not self.ai_processor.ai_client:
                return self.generate_basic_analysis(query_result)
            
            formatted_results = self.format_results_for_analysis(query_result)
            
            prompt = f"""
    # 分析任务：
    请根据以下信息分析查询结果并回答用户的问题。
    # 用户原始问题：
    {user_message}
    # 执行的SQL查询：
    {sql_query}
    # 查询结果（共{len(query_result)}条记录）：
    {formatted_results}
    # 分析要求：
    1. 总结查询结果的主要发现
    2. 分析数据趋势和模式（如有）
    3. 用中文回复，专业且易懂
    4. 如果无数据，说明原因并建议
    请直接回复分析结果：
    """
            
            try:
                response = self.ai_processor.ai_client.chat.completions.create(
                    model=self.ai_processor.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=800,
                    temperature=0.3,
                    timeout=60  # 增加超时时间到60秒
                )
                
                return response.choices[0].message.content
                
            except Exception as ai_error:
                logger.warning(f"⚠️ AI分析超时或失败，使用基础分析: {ai_error}")
                return self.generate_enhanced_analysis(query_result, user_message)
                
        except Exception as e:
            logger.error(f"❌ AI分析结果失败: {e}")
            return self.generate_basic_analysis(query_result)
        


    def format_final_response(self, user_message, sql_generation, query_result, analysis_result):
        """格式化最终响应 - 美化显示格式"""
        preview_table = self.generate_preview_table(query_result)
        
        # 美化分析结果显示
        formatted_analysis = self.beautify_analysis_output(analysis_result)
        
        response_data = {
            'status': 'success',
            'response_type': 'intelligent_sql_analysis',
            'message': f"""
    <div class="intelligent-analysis-result">
        <div class="analysis-header bg-primary text-white p-3 rounded-top">
            <div class="d-flex align-items-center">
                <i class="bi bi-robot fs-4 me-2"></i>
                <h4 class="mb-0">🤖 智能分析结果</h4>
            </div>
            <small>基于您的查询条件，已找到 {len(query_result)} 条相关记录</small>
        </div>
        
        <div class="analysis-body p-4">
            {formatted_analysis}
        </div>
        
        <div class="analysis-technical bg-light p-3 border-top">
            <div class="sql-info mb-3">
                <h5 class="d-flex align-items-center">
                    <i class="bi bi-database me-2"></i>执行的SQL查询
                </h5>
                <div class="sql-code-container">
                    <button class="btn btn-sm btn-outline-secondary mb-2 copy-sql-btn" 
                            onclick="copyToClipboard(this)">
                        <i class="bi bi-clipboard"></i> 复制SQL
                    </button>
                    <pre class="bg-light p-3 border rounded"><code>{sql_generation['sql_query']}</code></pre>
                </div>
            </div>
            
            <div class="data-preview">
                <h5 class="d-flex align-items-center">
                    <i class="bi bi-table me-2"></i>数据预览（共 {len(query_result)} 条记录）
                </h5>
                {preview_table}
            </div>
        </div>
    </div>
            """,
            'data_count': len(query_result),
            'sql_query': sql_generation['sql_query'],
            'tables_used': sql_generation['tables_used']
        }
        
        return response_data
    def beautify_analysis_output(self, analysis_text):
        """美化AI分析结果的显示"""
        if not analysis_text:
            return '<div class="alert alert-warning">暂无分析结果</div>'
        
        # 处理Markdown格式为HTML
        formatted_html = self.markdown_to_html(analysis_text)
        
        return f"""
        <div class="analysis-content">
            <div class="analysis-text">
                {formatted_html}
            </div>
        </div>
        """
    def markdown_to_html(self, markdown_text):
        """将Markdown格式转换为美化HTML"""
        import re
        
        # 替换标题
        markdown_text = re.sub(r'### (.*?)(?=\n|$)', r'<h5 class="text-primary mt-4">\1</h5>', markdown_text)
        markdown_text = re.sub(r'## (.*?)(?=\n|$)', r'<h4 class="text-primary mt-4 border-bottom pb-2">\1</h4>', markdown_text)
        markdown_text = re.sub(r'# (.*?)(?=\n|$)', r'<h3 class="text-primary mt-4 border-bottom pb-2">\1</h3>', markdown_text)
        
        # 替换列表项
        markdown_text = re.sub(r'\* (.*?)(?=\n|$)', r'<li class="mb-1">\1</li>', markdown_text)
        markdown_text = re.sub(r'(<li.*?</li>\s*)+', r'<ul class="list-unstyled ms-3">\g<0></ul>', markdown_text, flags=re.DOTALL)
        
        # 替换粗体
        markdown_text = re.sub(r'\*\*(.*?)\*\*', r'<strong class="text-dark">\1</strong>', markdown_text)
        
        # 替换段落
        paragraphs = re.split(r'\n\s*\n', markdown_text)
        formatted_paragraphs = []
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            # 如果已经是HTML标签，不处理
            if para.startswith('<') and para.endswith('>'):
                formatted_paragraphs.append(para)
            else:
                # 检查是否是列表
                if para.startswith('<ul>'):
                    formatted_paragraphs.append(para)
                else:
                    formatted_paragraphs.append(f'<p class="mb-3">{para}</p>')
        
        return '\n'.join(formatted_paragraphs)

    









    # 辅助方法
    def extract_sql_from_ai_response(self, ai_content):
        """从AI响应中提取SQL语句"""
        import re
        
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
        import re
        tables = re.findall(r'FROM\s+(\w+)', sql_query, re.IGNORECASE)
        tables.extend(re.findall(r'JOIN\s+(\w+)', sql_query, re.IGNORECASE))
        return list(set(tables))
    
    def format_results_for_analysis(self, query_result, max_records=50):
        """格式化查询结果用于AI分析"""
        import json
        from decimal import Decimal
        import datetime  # 修复这里的导入
        
        if not query_result:
            return "无查询结果"
        
        # 显示所有记录，或者设置一个较大的上限
        display_results = query_result[:max_records]
        
        result_text = f"共找到 {len(query_result)} 条记录\n\n"
        
        for i, record in enumerate(display_results, 1):
            result_text += f"记录{i}:\n"
            for key, value in record.items():
                # 处理特殊数据类型
                if isinstance(value, datetime.datetime):
                    value = value.isoformat()
                elif isinstance(value, datetime.date):
                    value = value.isoformat()
                elif isinstance(value, Decimal):
                    value = float(value)
                elif value is None:
                    value = "NULL"
                
                # 完整显示所有内容，不进行截断
                result_text += f"  {key}: {value}\n"
            result_text += "\n"
        
        # 如果记录总数超过显示数量，提示还有多少条未显示
        if len(query_result) > len(display_results):
            remaining = len(query_result) - len(display_results)
            result_text += f"... 还有 {remaining} 条记录未显示\n"
        
        return result_text
    

    

    def generate_preview_table(self, query_result, max_display=None):  # max_display设为None显示全部
        """生成数据预览表格 - 显示完整内容，不加省略号"""
        if not query_result:
            return "<p>无数据</p>"
        
        display_data = query_result  # 显示所有数据
        
        if not display_data:
            return "<p>无数据</p>"
        
        # 获取列名
        columns = list(display_data[0].keys())
        
        table_html = f'<div class="table-responsive" style="max-height: 600px; overflow-y: auto;"><table class="table table-sm table-bordered table-striped">'
        table_html += '<thead><tr class="table-primary">'
        for col in columns:
            table_html += f'<th class="text-nowrap">{col}</th>'
        table_html += '</tr></thead><tbody>'
        
        for row in display_data:
            table_html += '<tr>'
            for col in columns:
                value = row.get(col, '')
                # 处理特殊数据类型
                if isinstance(value, (dict, list)):
                    import json
                    try:
                        value = f'<pre style="margin:0; white-space:pre-wrap;">{json.dumps(value, ensure_ascii=False, indent=2)}</pre>'
                    except:
                        value = f'<pre style="margin:0; white-space:pre-wrap;">{str(value)}</pre>'
                elif value is None:
                    value = '<span class="text-muted"><em>NULL</em></span>'
                elif isinstance(value, str) and value.strip().startswith(('{', '[')):
                    value = f'<pre style="margin:0; white-space:pre-wrap;">{value}</pre>'
                else:
                    # 普通文本，确保换行符等正确显示
                    value = f'<div style="white-space: pre-wrap;">{value}</div>'
                
                table_html += f'<td style="max-width: 400px; overflow: auto;">{value}</td>'
            table_html += '</tr>'
        
        table_html += '</tbody></table>'
        table_html += f'<div class="text-end mt-2"><small class="text-muted badge bg-secondary">共 {len(query_result)} 条记录</small></div>'
        table_html += '</div>'
        
        return table_html

    def generate_basic_analysis(self, query_result):
        """生成基础分析"""
        if not query_result:
            return "未找到相关数据。"
        
        return f"找到 {len(query_result)} 条相关记录。建议使用更具体的查询条件来缩小范围。"

    def error_response_dict(self, message):
        """错误响应"""
        return {
            'status': 'error',
            'message': f'<div class="alert alert-danger">{message}</div>'
        }
    

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
            schema_understanding = self.help_ai_understand_schema()
            
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
