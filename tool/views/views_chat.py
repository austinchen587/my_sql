# tool/views/views_chat.py

import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import connection
from django.conf import settings
from django.shortcuts import render
from datetime import datetime

# 替代方案：条件导入
try:
    import openai
except ImportError:
    openai = None
    logging.warning("openai库未安装")

logger = logging.getLogger(__name__)


class ChatMessageProcessor:
    """聊天消息处理器 - 处理前端发送的所有消息"""
    def __init__(self):
        self.ai_client = None
        self.setup_ai_client()

    def setup_ai_client(self):
        """设置AI客户端"""
        try:
            # 可以使用硅基流动或其他AI服务
            # 这里使用OpenAI兼容的API
            if hasattr(settings, 'AI_API_KEY') and settings.AI_API_KEY:
                self.ai_client = openai.OpenAI(
                    api_key=settings.AI_API_KEY,
                    base_url=getattr(settings, 'AI_API_BASE', 'https://api.siliconflow.cn/v1')
                )
        except Exception as e:
            logger.warning(f"AI客户端初始化失败: {e}")


    def process_message(self, request_data):
        """处理消息路由"""
        message = request_data.get('message', '').strip()
        message_type = request_data.get('message_type', 'normal_chat')
        
        logger.info(f"收到消息: {message[:100]}, 类型: {message_type}")
        
        if message_type == 'data_analysis' or message.endswith('#psql'):
            return self.handle_data_analysis(message)
        else:
            return self.handle_normal_chat(message)
        

    def handle_data_analysis(self, user_message):
        """处理数据分析请求"""
        try:
            # 移除#psql标记
            clean_message = user_message.replace('#psql', '').strip()
            
            # 步骤1: 使用AI生成SQL查询
            sql_query = self.generate_sql_query(clean_message)
            if not sql_query:
                return self.error_response("无法生成有效的SQL查询")
            
            # 步骤2: 执行SQL查询
            query_result = self.execute_sql_query(sql_query)
            if query_result is None:
                return self.error_response("数据库查询失败")
            
            # 步骤3: 使用AI分析查询结果
            analysis_result = self.analyze_query_results(clean_message, query_result)
            
            return self.success_data_analysis_response(
                sql_query=sql_query,
                data=query_result,
                analysis=analysis_result
            )
            
        except Exception as e:
            logger.error(f"数据分析处理失败: {e}")
            return self.error_response(f"数据分析失败: {str(e)}")
        

    def generate_sql_query(self, natural_language_query):
       """使用AI将自然语言转换为SQL查询 - 优化版本"""
       try:
           # 数据库表结构提示词
           schema_prompt = self.get_database_schema_prompt()
        
           # 更明确的指令
           prompt = f"""
           你是专业的SQL专家。请根据提供的数据库结构，将用户的中文问题转换为准确、高效的PostgreSQL查询语句。
           数据库结构信息:
           {schema_prompt}
           用户问题: {natural_language_query}
           转换要求:
           1. 必须基于base_procurement_info表进行查询
           2. 只返回纯SQL语句，不要包含任何解释文字
           3. 使用PostgreSQL语法，确保语法正确
           4. 包含适当的WHERE条件过滤
           5. 限制结果在100条以内（使用LIMIT 100）
           6. 对于时间查询，优先使用publish_time字段
           7. 项目类型通过title字段的LIKE条件识别
           特别注意：
           - 医疗项目：title LIKE '%医疗%' OR title LIKE '%医院%'等
           - 采购意向：info_type可能包含相关关键词
           - 时间范围：使用EXTRACT函数提取年月
           直接返回SQL语句：
           """
        
           if self.ai_client:
               response = self.ai_client.chat.completions.create(
                   model=getattr(settings, 'AI_MODEL', 'gpt-3.5-turbo'),
                   messages=[{"role": "user", "content": prompt}],
                   max_tokens=500,
                   temperature=0.1
               )
               sql_query = response.choices[0].message.content.strip()
            
               # 更严格的SQL清理
               sql_query = self.clean_sql_query(sql_query)
            
               # 验证SQL基本格式
               if not self.validate_sql_basic(sql_query):
                   logger.warning(f"SQL格式验证失败，使用备用方案: {sql_query}")
                   return self.fallback_sql_generation(natural_language_query)
                
               return sql_query
           else:
               return self.fallback_sql_generation(natural_language_query)
            
       except Exception as e:
           logger.error(f"SQL生成失败: {e}")
           return self.fallback_sql_generation(natural_language_query)
       

    def clean_sql_query(self, sql_query):
       """清理SQL查询语句"""
       # 移除markdown代码块
       if sql_query.startswith('```sql'):
           sql_query = sql_query[6:]
       if sql_query.endswith('```'):
           sql_query = sql_query[:-3]
    
       # 移除可能的SELECT前缀说明
       lines = sql_query.strip().split('\n')
       clean_lines = []
       for line in lines:
           if not line.lower().startswith('select') and 'select' in line.lower():
               # 找到真正的SELECT开始
               select_index = line.lower().find('select')
               line = line[select_index:]
           clean_lines.append(line)
    
       return '\n'.join(clean_lines).strip()
    def validate_sql_basic(self, sql_query):
        """基本SQL验证"""
        sql_upper = sql_query.upper().strip()
        return sql_upper.startswith('SELECT') and 'FROM' in sql_upper

        
    
    def get_database_schema_prompt(self):
       """获取数据库表结构提示词 - 优化版本"""
       return """
       表名: base_procurement_info
       关键字段:
      - url (主键, VARCHAR)
      - title (标题, VARCHAR) - 包含项目名称和类型信息
      - jurisdiction (管辖区域, VARCHAR)
      - info_type (信息类型: 招标公告/中标公告/采购意向等)
      - bid_type (招标类型, VARCHAR)
      - publish_time (发布时间，DATE类型)
      - budget_amount (预算金额，NUMERIC)
      - max_price_limit (最高限价，NUMERIC)
      - purchaser_name (采购人名称, VARCHAR)
      - agency_name (代理机构, VARCHAR)
      - is_active (是否有效, BOOLEAN)
      - project_name (项目名称, VARCHAR)
      - project_overview (项目概述, TEXT)
      - procurement_items (采购项目清单, JSONB)
    重要说明:
    1. 项目类型识别：通过title字段识别项目类别，如：
       - 医疗项目：title包含"医疗"、"医院"、"医疗器械"、"药品"等
       - 工程项目：title包含"工程"、"建设"、"施工"等
       - IT项目：title包含"系统"、"软件"、"信息化"等
    
    2. 采购意向查询：info_type可能包含"采购意向公告"类型
    
    3. 时间查询示例：
       - 11月份数据：EXTRACT(MONTH FROM publish_time) = 11
       - 指定年份：EXTRACT(YEAR FROM publish_time) = 2024
    4. 医疗项目查询示例：
       SELECT title, publish_time, budget_amount, purchaser_name 
       FROM base_procurement_info 
       WHERE (title LIKE '%医疗%' OR title LIKE '%医院%' OR title LIKE '%药品%' OR title LIKE '%器械%')
       AND EXTRACT(MONTH FROM publish_time) = 11
       AND EXTRACT(YEAR FROM publish_time) = 2024
       AND is_active = true
       LIMIT 100;
    索引:
      - idx_publish_time (发布时间索引)
      - idx_info_type (信息类型索引)
      - idx_type_publish_time (复合索引)
    """
        

    
    
    def fallback_sql_generation(self, query):
        """备用SQL生成方案（基于关键词）"""
        query_lower = query.lower()
        
        # 基础查询模板
        base_sql = "SELECT url, title, publish_time, budget_amount, purchaser_name FROM base_procurement_info WHERE is_active = true"
        
        # 关键词匹配
        conditions = []
        
        if '招标' in query_lower or '采购' in query_lower:
            conditions.append("info_type LIKE '%招标%'")
        elif '中标' in query_lower:
            conditions.append("info_type LIKE '%中标%'")
        elif '公告' in query_lower:
            conditions.append("info_type LIKE '%公告%'")
        
        if '最近' in query_lower or '最新' in query_lower:
            if '月' in query_lower:
                conditions.append("publish_time >= CURRENT_DATE - INTERVAL '1 month'")
            elif '周' in query_lower:
                conditions.append("publish_time >= CURRENT_DATE - INTERVAL '7 days'")
            else:
                conditions.append("publish_time >= CURRENT_DATE - INTERVAL '30 days'")
        
        if '金额' in query_lower or '预算' in query_lower:
            if '大' in query_lower or '高' in query_lower:
                base_sql = base_sql.replace("SELECT url, title, publish_time, budget_amount, purchaser_name", 
                                          "SELECT url, title, publish_time, budget_amount, purchaser_name")
                conditions.append("budget_amount IS NOT NULL")
                base_sql += " ORDER BY budget_amount DESC"
        
        if conditions:
            base_sql += " AND " + " AND ".join(conditions)
        
        base_sql += " LIMIT 50"
        return base_sql
    

    def execute_sql_query(self, sql_query):
        """执行SQL查询并返回结果"""
        try:
            with connection.cursor() as cursor:
                # 安全性检查：确保是SELECT查询
                if not sql_query.strip().upper().startswith('SELECT'):
                    logger.warning(f"非SELECT查询被拒绝: {sql_query}")
                    return None
                
                cursor.execute(sql_query)
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                
                # 转换为字典列表
                result = []
                for row in rows:
                    result.append(dict(zip(columns, row)))
                
                logger.info(f"SQL查询成功，返回 {len(result)} 条记录")
                return result
                
        except Exception as e:
            logger.error(f"SQL执行失败: {e}, 查询: {sql_query}")
            return None
        

    def analyze_query_results(self, original_query, query_results):
        """使用AI分析查询结果"""
        try:
            if not query_results:
                return "查询未返回任何结果。"
            
            # 构建分析提示词
            prompt = f"""
            基于以下查询结果，为原始问题提供简要分析总结。
            原始问题: {original_query}
            查询结果摘要:
            - 总记录数: {len(query_results)}
            - 字段示例: {list(query_results[0].keys()) if query_results else []}
            - 前3条记录摘要: {str(query_results[:3])}
            请提供:
            1. 数据概况总结
            2. 关键发现或趋势
            3. 如有异常或特殊情况请指出
            分析结果:
            """
            
            if self.ai_client:
                response = self.ai_client.chat.completions.create(
                    model=getattr(settings, 'AI_MODEL', 'gpt-3.5-turbo'),
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500,
                    temperature=0.7
                )
                return response.choices[0].message.content.strip()
            else:
                return self.fallback_analysis(original_query, query_results)
                
        except Exception as e:
            logger.error(f"结果分析失败: {e}")
            return f"数据分析完成，共{len(query_results)}条记录。"
        

    def fallback_analysis(self, original_query, query_results):
        """备用分析方案"""
        summary = f"查询成功，共找到 {len(query_results)} 条相关记录。"
        
        if query_results:
            # 简单的统计信息
            budget_values = [r.get('budget_amount', 0) for r in query_results if r.get('budget_amount')]
            if budget_values:
                avg_budget = sum(budget_values) / len(budget_values)
                summary += f" 平均预算金额: {avg_budget:,.2f}元。"
            
            # 时间范围
            publish_times = [r.get('publish_time') for r in query_results if r.get('publish_time')]
            if publish_times:
                latest = max(publish_times)
                summary += f" 最新记录时间: {latest}。"
        
        return summary
    

    def handle_normal_chat(self, message):
        """处理普通聊天消息"""
        try:
            if self.ai_client:
                response = self.ai_client.chat.completions.create(
                    model=getattr(settings, 'AI_MODEL', 'gpt-3.5-turbo'),
                    messages=[{"role": "user", "content": message}],
                    max_tokens=1000,
                    temperature=0.7
                )
                return self.success_chat_response(response.choices[0].message.content)
            else:
                return self.success_chat_response("AI服务暂不可用，请检查配置。")
                
        except Exception as e:
            logger.error(f"普通聊天处理失败: {e}")
            return self.error_response(f"聊天服务暂时不可用: {str(e)}")
        

    def success_data_analysis_response(self, sql_query, data, analysis):
        """成功的数据分析响应"""
        return JsonResponse({
            'status': 'data_analysis',
            'sql_query': sql_query,
            'data': data,
            'analysis': analysis,
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
        # 返回聊天页面
        return render(request, 'tool/chat.html')
    
    elif request.method == 'POST':
        # 处理API请求
        try:
            # 解析JSON数据
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST
            
            # 处理消息
            return chat_processor.process_message(data)
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'error': '无效的JSON数据'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'error': '服务器内部错误'}, status=500)