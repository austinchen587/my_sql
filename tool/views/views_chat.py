# tool/views/views_chat.py

import json
import logging
import os

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import connection
from django.conf import settings
from django.shortcuts import render
from datetime import datetime

logger = logging.getLogger(__name__)


class ChatMessageProcessor:
    """聊天消息处理器 - 处理前端发送的所有消息"""
    def __init__(self):
        self.ai_client = None
        self.setup_ai_client()

    def setup_ai_client(self):
        """设置AI客户端 - 增强错误处理"""
        try:
            # 检查配置是否存在
            if not hasattr(settings, 'AI_API_KEY') or not settings.AI_API_KEY or settings.AI_API_KEY == 'your-siliconflow-apikey':
                logger.warning("AI_API_KEY未正确配置，将使用本地SQL生成")
                return
            
            # 尝试导入openai库
            try:
                import openai
            except ImportError:
                logger.warning("openai库未安装，将使用本地SQL生成")
                openai = None
                return
            
            # 获取配置
            api_base = getattr(settings, 'AI_API_BASE', 'https://api.siliconflow.cn/v1')
            api_key = settings.AI_API_KEY
            model_name = getattr(settings, 'AI_MODEL', 'deepseek-ai/DeepSeek-V3.1-Terminus')
            
            logger.info(f"初始化AI客户端，API Base: {api_base}, Model: {model_name}")
            
            self.ai_client = openai.OpenAI(
                api_key=api_key,
                base_url=api_base
            )
            
            # 保存模型名称供后续使用
            self.model_name = model_name
            
            # 测试连接
            if self.test_ai_connection():
                logger.info("AI客户端初始化成功")
            else:
                logger.warning("AI客户端连接测试失败，将使用本地SQL生成")
                self.ai_client = None
                
        except Exception as e:
            logger.error(f"AI客户端初始化失败: {e}")
            self.ai_client = None

    def test_ai_connection(self):
        """测试AI连接"""
        try:
            if not self.ai_client:
                return False
                
            # 简单的连接测试
            self.ai_client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "测试"}],
                max_tokens=10
            )
            return True
        except Exception as e:
            logger.error(f"AI连接测试失败: {e}")
            return False

    def process_message(self, request_data):
        """处理消息路由"""
        message = request_data.get('message', '').strip()
        message_type = request_data.get('message_type', 'normal_chat')
        
        logger.info(f"收到消息: {message[:100]}, 类型: {message_type}")
        
        # 检查是否包含#psql标记（支持空格和紧凑格式）
        has_psql_marker = (
            message_type == 'data_analysis' or 
            '#psql' in message.lower() or 
            '#p s q l' in message.lower()
        )
        
        if has_psql_marker:
            return self.handle_data_analysis(message)
        else:
            return self.handle_normal_chat(message)

    def handle_data_analysis(self, user_message):
        """处理数据分析请求"""
        try:
            # 清理消息，移除各种psql标记
            clean_message = self.clean_psql_marker(user_message)
            
            # 步骤1: 智能选择查询表（支持跨表查询判断）
            target_tables = self.select_target_tables(clean_message)
            logger.info(f"选择查询表: {target_tables}")
            
            # 步骤2: 使用AI或本地生成SQL查询
            sql_query = self.generate_sql_query(clean_message, target_tables)
            if not sql_query:
                return self.error_response("无法生成有效的SQL查询")
            
            logger.info(f"生成的SQL: {sql_query}")
            
            # 步骤3: 执行SQL查询
            query_result = self.execute_sql_query(sql_query)
            if query_result is None:
                return self.error_response("数据库查询失败")
            
            # 步骤4: 分析查询结果
            analysis_result = self.analyze_query_results(clean_message, query_result, target_tables)
            
            return self.success_data_analysis_response(
                sql_query=sql_query,
                data=query_result,
                analysis=analysis_result,
                table_used=target_tables[0] if isinstance(target_tables, list) else target_tables
            )
            
        except Exception as e:
            logger.error(f"数据分析处理失败: {e}")
            return self.error_response(f"数据分析失败: {str(e)}")

    def clean_psql_marker(self, message):
        """清理消息中的psql标记"""
        # 移除各种格式的psql标记
        markers = ['#psql', '#p s q l', '#PSQL', '#P S Q L']
        cleaned = message
        for marker in markers:
            cleaned = cleaned.replace(marker, '')
        return cleaned.strip()

    def select_target_tables(self, user_message):
        """根据用户查询内容智能选择目标表（支持跨表查询判断）"""
        message_lower = user_message.lower()
        
        # 判断是否需要跨表查询
        needs_cross_table = self.needs_cross_table_query(message_lower)
        if needs_cross_table:
            return ['base_procurement_info_new', 'procurement_intention']
        
        # 精确的关键词匹配逻辑
        if any(word in message_lower for word in ['意向', '预算金额', '采购单位', '预计时间', '采购意向', '预算']):
            return 'procurement_intention'
        elif any(word in message_lower for word in ['公告内容', '详细内容', '完整内容', 'json格式', 'content', '全文']):
            return 'procurement_notices'
        elif any(word in message_lower for word in ['招标公告', '中标公示', '基础信息', '采购信息', '基本信息']):
            return 'base_procurement_info_new'
        else:
            # 默认选择基础信息表
            return 'base_procurement_info_new'

    def needs_cross_table_query(self, message_lower):
        """判断是否需要跨表查询"""
        # 如果查询同时涉及基础信息和意向信息
        base_info_keywords = ['招标', '中标', '公告', '采购信息']
        intention_keywords = ['预算', '金额', '采购单位', '意向']
        
        has_base_info = any(keyword in message_lower for keyword in base_info_keywords)
        has_intention_info = any(keyword in message_lower for keyword in intention_keywords)
        
        return has_base_info and has_intention_info

    def generate_sql_query(self, natural_language_query, target_tables):
        """生成SQL查询 - 支持单表和跨表查询"""
        # 如果有AI客户端且连接正常，使用AI生成
        if self.ai_client:
            return self.generate_sql_with_ai(natural_language_query, target_tables)
        else:
            # 使用本地SQL生成
            return self.generate_sql_locally(natural_language_query, target_tables)

    def generate_sql_with_ai(self, natural_language_query, target_tables):
        """使用AI生成SQL查询 - 支持跨表查询"""
        try:
            if isinstance(target_tables, list):
                # 跨表查询
                schema_prompt = self.get_cross_table_schema_prompt(target_tables)
            else:
                # 单表查询
                schema_prompt = self.get_database_schema_prompt(target_tables)
            
            requested_fields = self.identify_requested_fields(natural_language_query)
        
            prompt = f"""
你是一个专业的SQL专家，需要根据用户的中文查询生成精确的PostgreSQL语句。

数据库表结构：
{schema_prompt}

用户查询："{natural_language_query}"

要求：
1. 基于上述表结构进行查询
2. SELECT子句只包含用户明确要求的字段，不要添加额外字段
3. 使用PostgreSQL语法，确保语法正确性
4. 包含与查询内容相关的WHERE条件
5. 限制结果为100条以内（使用LIMIT 100）
6. 对于时间查询，优先使用publish_time字段
7. 只返回纯SQL语句，不要包含任何解释
8. 注意不同表的时间字段差异：
   - base_procurement_info_new 和 procurement_intention 使用 publish_time
   - procurement_notices 同时有 publish_time 和 crawl_time，查询时使用 publish_time

用户可能需要的字段：{requested_fields if requested_fields else '根据查询内容确定'}

请直接返回SQL语句：
"""
        
            response = self.ai_client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600,
                temperature=0.1
            )
            sql_query = response.choices[0].message.content.strip()
            
            # 清理SQL
            sql_query = self.clean_sql_query(sql_query)
            
            # 验证SQL格式
            if self.validate_sql_basic(sql_query):
                return sql_query
            else:
                logger.warning(f"AI生成的SQL格式验证失败，使用本地生成")
                return self.generate_sql_locally(natural_language_query, target_tables)
            
        except Exception as e:
            logger.error(f"AI SQL生成失败: {e}")
            return self.generate_sql_locally(natural_language_query, target_tables)

    def generate_sql_locally(self, natural_language_query, target_tables):
        """本地SQL生成方案 - 支持单表和简单跨表查询"""
        query_lower = natural_language_query.lower()
        
        if isinstance(target_tables, list):
            # 简单的跨表查询（LEFT JOIN）
            return self.generate_cross_table_sql(query_lower, target_tables)
        else:
            # 单表查询
            return self.generate_single_table_sql(query_lower, target_tables)

    def generate_single_table_sql(self, query_lower, target_table):
        """生成单表SQL查询"""
        # 识别用户需要的字段
        requested_fields = self.identify_requested_fields_by_table(query_lower, target_table)
        
        # 根据目标表和用户需求选择字段
        if requested_fields:
            # 确保url字段始终包含（作为标识）
            if 'url' not in requested_fields:
                requested_fields.insert(0, 'url')
            select_fields = ', '.join(requested_fields)
        else:
            # 默认字段选择
            select_fields = self.get_default_fields_by_table(target_table)
        
        base_sql = f"SELECT {select_fields} FROM {target_table} WHERE 1=1"
        
        # 构建条件
        conditions = self.build_sql_conditions(query_lower, target_table)
        
        if conditions:
            base_sql += " AND " + " AND ".join(conditions)
        
        # 添加排序
        base_sql = self.add_ordering(base_sql, query_lower, target_table)
        
        base_sql += " LIMIT 100"
        return base_sql

    def generate_cross_table_sql(self, query_lower, target_tables):
        """生成跨表SQL查询（基础信息表 + 意向表）"""
        # 简单的LEFT JOIN查询
        base_sql = """
SELECT 
    base.url, base.title, base.jurisdiction, base.info_type, base.publish_time,
    intention.intention_budget_amount, intention.intention_procurement_unit
FROM base_procurement_info_new base
LEFT JOIN procurement_intention intention ON base.url = intention.url
WHERE 1=1
"""
        
        conditions = []
        
        # 基础信息表条件
        if '招标' in query_lower:
            conditions.append("base.info_type LIKE '%招标%'")
        elif '中标' in query_lower:
            conditions.append("base.info_type LIKE '%中标%'")
        
        # 意向表条件
        if '预算' in query_lower or '金额' in query_lower:
            conditions.append("intention.intention_budget_amount IS NOT NULL")
        
        if conditions:
            base_sql += " AND " + " AND ".join(conditions)
        
        if '预算' in query_lower or '金额' in query_lower:
            base_sql += " ORDER BY intention.intention_budget_amount DESC"
        else:
            base_sql += " ORDER BY base.publish_time DESC"
        
        base_sql += " LIMIT 100"
        return base_sql

    def identify_requested_fields(self, natural_language_query):
        """识别用户查询中明确要求的字段"""
        query_lower = natural_language_query.lower()
        requested_fields = []
        
        # 通用字段映射
        field_mapping = {
            '标题': 'title',
            '网址': 'url',
            '链接': 'url',
            '管辖区域': 'jurisdiction',
            '信息类型': 'info_type',
            '招标类型': 'bid_type',
            '发布时间': 'publish_time',
        }
        
        # 意向表专用字段
        intention_field_mapping = {
            '预算金额': 'intention_budget_amount',
            '采购单位': 'intention_procurement_unit',
            '项目名称': 'intention_project_name',
            '预计时间': 'intention_estimated_time',
        }
        
        # 公告表专用字段
        notice_field_mapping = {
            '公告内容': 'content',
            '爬取时间': 'crawl_time',
        }
        
        # 合并所有字段映射
        all_mappings = {**field_mapping, **intention_field_mapping, **notice_field_mapping}
        
        for chinese_field, db_field in all_mappings.items():
            if chinese_field in query_lower:
                requested_fields.append(db_field)
        
        return requested_fields if requested_fields else None

    def identify_requested_fields_by_table(self, query_lower, target_table):
        """根据表识别用户需要的字段"""
        requested_fields = []
        
        # 基础字段（三张表共有）
        base_fields = {
            '标题': 'title',
            '网址': 'url',
            '管辖区域': 'jurisdiction',
            '信息类型': 'info_type',
            '发布时间': 'publish_time',
        }
        
        # 表特定字段
        table_specific_fields = {
            'procurement_intention': {
                '预算金额': 'intention_budget_amount',
                '采购单位': 'intention_procurement_unit',
                '项目名称': 'intention_project_name',
            },
            'procurement_notices': {
                '公告内容': 'content',
                '爬取时间': 'crawl_time',
            }
        }
        
        # 添加基础字段
        for chinese_field, db_field in base_fields.items():
            if chinese_field in query_lower:
                requested_fields.append(db_field)
        
        # 添加表特定字段
        if target_table in table_specific_fields:
            for chinese_field, db_field in table_specific_fields[target_table].items():
                if chinese_field in query_lower:
                    requested_fields.append(db_field)
        
        return requested_fields

    def get_default_fields_by_table(self, target_table):
        """根据表获取默认查询字段"""
        default_fields = {
            'base_procurement_info_new': 'url, title, publish_time, jurisdiction, info_type',
            'procurement_intention': 'url, title, publish_time, intention_budget_amount, intention_procurement_unit',
            'procurement_notices': 'url, title, publish_time, info_type, jurisdiction'
        }
        return default_fields.get(target_table, 'url, title, publish_time')

    def build_sql_conditions(self, query_lower, target_table):
        """构建SQL条件"""
        conditions = []
        
        # 日期处理
        if '11月10' in query_lower or '11月10日' in query_lower:
            conditions.append("EXTRACT(MONTH FROM publish_time) = 11")
            conditions.append("EXTRACT(DAY FROM publish_time) = 10")
        elif '11月' in query_lower or '十一月' in query_lower:
            conditions.append("EXTRACT(MONTH FROM publish_time) = 11")
        
        # 年份处理
        current_year = datetime.now().year
        if str(current_year) in query_lower:
            conditions.append(f"EXTRACT(YEAR FROM publish_time) = {current_year}")
        elif '今年' in query_lower:
            conditions.append(f"EXTRACT(YEAR FROM publish_time) = {current_year}")
        
        # 信息类型匹配
        if '招标公告' in query_lower:
            conditions.append("info_type LIKE '%招标公告%'")
        elif '招标' in query_lower:
            conditions.append("info_type LIKE '%招标%'")
        elif '中标' in query_lower:
            conditions.append("info_type LIKE '%中标%'")
        elif '采购意向' in query_lower:
            conditions.append("info_type LIKE '%意向%'")
        
        # 特定表条件
        if target_table == 'procurement_intention' and ('预算' in query_lower or '金额' in query_lower):
            conditions.append("intention_budget_amount IS NOT NULL")
        
        return conditions

    def add_ordering(self, base_sql, query_lower, target_table):
        """添加排序条件"""
        if ('金额' in query_lower or '预算' in query_lower) and target_table == 'procurement_intention':
            base_sql += " ORDER BY intention_budget_amount DESC"
        elif '最新' in query_lower or '最近' in query_lower:
            base_sql += " ORDER BY publish_time DESC"
        return base_sql

    def clean_sql_query(self, sql_query):
        """清理SQL查询语句"""
        # 移除markdown代码块
        if sql_query.startswith('```sql'):
            sql_query = sql_query[6:]
        if sql_query.endswith('```'):
            sql_query = sql_query[:-3]
        
        # 移除注释和多余空格
        lines = sql_query.strip().split('\n')
        clean_lines = []
        for line in lines:
            line = line.split('--')[0].strip()
            if line and not line.startswith('--'):
                clean_lines.append(line)
        
        return ' '.join(clean_lines).strip()

    def validate_sql_basic(self, sql_query):
        """基本SQL验证"""
        sql_upper = sql_query.upper().strip()
        return sql_upper.startswith('SELECT') and 'FROM' in sql_upper

    def get_database_schema_prompt(self, table_name):
        """获取单表结构提示词"""
        schema_prompts = {
            'base_procurement_info_new': """
表名: base_procurement_info_new (基础采购信息表)
表关系: 基础表，存储通用采购信息字段
核心字段:
- url (主键): 采购信息原始URL
- title: 采购项目标题
- jurisdiction: 管辖区域
- info_type: 信息类型（招标公告、中标公示等）
- bid_type: 招标类型
- publish_time: 发布时间
时间字段说明: 使用publish_time进行时间查询
            """,
            
            'procurement_intention': """
表名: procurement_intention (采购意向表)
表关系: 在基础字段上扩展了意向相关字段
核心字段:
- url (主键): 采购意向公告URL
- title: 采购意向公告标题
- jurisdiction: 采购意向所属地区
- info_type: 信息类型（固定为采购意向）
- publish_time: 意向公告发布日期
扩展字段:
- intention_budget_amount: 采购项目预算金额（重要字段）
- intention_procurement_unit: 发起采购的单位名称
- intention_project_name: 采购项目名称
时间字段说明: 使用publish_time进行时间查询
            """,
            
            'procurement_notices': """
表名: procurement_notices (采购公告表)
表关系: 重点存储公告内容（JSON格式）
核心字段:
- url (主键): 采购公告页URL
- title: 公告标题
- jurisdiction: 公告适用地区
- info_type: 公告类型
- publish_time: 公告正式发布日期
特色字段:
- content: 结构化存储的公告全文（JSON格式）
- crawl_time: 数据抓取时间点
时间字段说明: 查询时使用publish_time，crawl_time为技术字段
            """
        }
        
        return schema_prompts.get(table_name, schema_prompts['base_procurement_info_new'])

    def get_cross_table_schema_prompt(self, tables):
        """获取跨表查询结构提示词"""
        return """
数据库表关系说明：

1. base_procurement_info_new (基础采购信息表)
   - 存储通用采购信息字段
   - 核心字段: url, title, jurisdiction, info_type, publish_time

2. procurement_intention (采购意向表)
   - 在基础字段上扩展了意向相关字段
   - 核心字段: url, title, 以及意向专用字段（预算金额、采购单位等）
   - 通过url字段与基础表关联

3. procurement_notices (采购公告表)
   - 重点存储公告内容（JSON格式）
   - 核心字段: url, title, 以及content字段存储详细信息

表关联关系：
- 三张表均通过url字段进行关联
- base_procurement_info_new 可作为关联基础表
- 跨表查询时使用LEFT JOIN ON url字段进行连接

时间字段统一性：
- 所有表都包含publish_time字段，用于时间范围查询
- procurement_notices表额外包含crawl_time字段（技术字段）

查询提示：优先使用publish_time进行时间条件过滤，注意字段在不同表中的一致性。
"""

    def execute_sql_query(self, sql_query):
        """执行SQL查询并返回结果"""
        try:
            with connection.cursor() as cursor:
                # 安全性检查
                sql_upper = sql_query.upper().strip()
                if not sql_upper.startswith('SELECT'):
                    logger.warning(f"非SELECT查询被拒绝: {sql_query}")
                    return None
                
                cursor.execute(sql_query)
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                
                # 转换为字典列表
                result = []
                for row in rows:
                    row_dict = {}
                    for i, col in enumerate(columns):
                        # 处理JSON字段
                        if isinstance(row[i], str) and col == 'content' and row[i].startswith('{'):
                            try:
                                row_dict[col] = json.loads(row[i])
                            except:
                                row_dict[col] = row[i]
                        else:
                            row_dict[col] = row[i]
                    result.append(row_dict)
                
                logger.info(f"SQL查询成功，返回 {len(result)} 条记录")
                return result
                
        except Exception as e:
            logger.error(f"SQL执行失败: {e}, 查询: {sql_query}")
            return None

    def analyze_query_results(self, original_query, query_results, target_tables):
        """分析查询结果"""
        try:
            if not query_results:
                return "查询未返回任何结果。"
            
            # 如果有AI客户端，使用AI分析
            if self.ai_client:
                prompt = f"""
基于以下查询结果，为原始问题提供简要分析总结。

原始查询: {original_query}
查询表: {target_tables}
总记录数: {len(query_results)}
返回字段: {list(query_results[0].keys()) if query_results else []}

请提供简洁的数据分析，重点关注数据趋势和关键发现：
"""
                
                response = self.ai_client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=300,
                    temperature=0.7
                )
                return response.choices[0].message.content.strip()
            else:
                # 本地分析
                return self.fallback_analysis(original_query, query_results)
                
        except Exception as e:
            logger.error(f"结果分析失败: {e}")
            return self.fallback_analysis(original_query, query_results)

    def fallback_analysis(self, original_query, query_results):
        """备用分析方案"""
        if not query_results:
            return "查询未返回任何结果。"
        
        summary = f"查询成功，共找到 {len(query_results)} 条相关记录。"
        
        if query_results:
            # 检查预算金额字段
            if 'intention_budget_amount' in query_results[0]:
                budget_values = [r.get('intention_budget_amount', 0) for r in query_results if r.get('intention_budget_amount') is not None]
                if budget_values:
                    avg_budget = sum(budget_values) / len(budget_values)
                    max_budget = max(budget_values)
                    summary += f" 预算金额范围: 平均{avg_budget:,.0f}元，最高{max_budget:,.0f}元。"
            
            # 时间范围分析
            if 'publish_time' in query_results[0]:
                publish_times = [r.get('publish_time') for r in query_results if r.get('publish_time')]
                if publish_times:
                    latest = max(publish_times)
                    oldest = min(publish_times)
                    summary += f" 时间跨度: {oldest} 至 {latest}。"
        
        return summary

    def handle_normal_chat(self, message):
        """处理普通聊天消息"""
        try:
            if self.ai_client:
                response = self.ai_client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": message}],
                    max_tokens=500,
                    temperature=0.7
                )
                return self.success_chat_response(response.choices[0].message.content)
            else:
                return self.success_chat_response(
                    "AI聊天服务当前不可用。如需查询数据，请在消息中包含 #psql 标记来使用本地SQL查询功能。"
                )
                
        except Exception as e:
            logger.error(f"普通聊天处理失败: {e}")
            return self.error_response("聊天服务暂时不可用")

    def success_data_analysis_response(self, sql_query, data, analysis, table_used):
        """成功的数据分析响应"""
        return JsonResponse({
            'status': 'data_analysis',
            'sql_query': sql_query,
            'data': data,
            'analysis': analysis,
            'table_used': table_used,
            'timestamp': datetime.now().isoformat()
        })

    def success_chat_response(self, response_text):
        """成功的聊天响应"""
        return JsonResponse({
            'status': 'success',
            'response': response_text,
            'timestamp': datetime.now().isoformat()
        })

    def error_response(self, error_message):
        """错误响应"""
        return JsonResponse({
            'status': 'error',
            'error': error_message,
            'timestamp': datetime.now().isoformat()
        })

# 创建全局处理器实例
chat_processor = ChatMessageProcessor()

@require_http_methods(["GET", "POST"])
def chat(request):
    """统一的chat视图：GET返回页面，POST处理消息"""
    
    if request.method == 'GET':
        return render(request, 'tool/chat.html')
    
    elif request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST
            
            return chat_processor.process_message(data)
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'error': '无效的JSON数据'}, status=400)
        except Exception as e:
            logger.error(f"服务器内部错误: {e}")
            return JsonResponse({'status': 'error', 'error': '服务器内部错误'}, status=500)
