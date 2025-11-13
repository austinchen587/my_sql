# tool/views/views_chat.py

import json
import logging
import re
import traceback
from collections import Counter
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import connection
from django.conf import settings
from django.shortcuts import render

logger = logging.getLogger(__name__)

# 全局变量，用于存储数据库结构认知状态
database_understanding_cache = {
    'last_updated': None,
    'schema_info': None,
    'sample_data': None
}

class ChatMessageProcessor:
    """聊天消息处理器 - 处理前端发送的所有消息"""
    
    def __init__(self):
        self.ai_client = None
        self.setup_ai_client()
        # 存储用户会话状态
        self.user_sessions = {}

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
        """处理消息路由 - 统一响应格式"""
        try:
            message = request_data.get('message', '').strip()
            message_type = request_data.get('message_type', 'normal_chat')
            session_id = request_data.get('session_id', 'default')
            
            logger.info(f"收到消息: {message[:100]}, 类型: {message_type}, 会话: {session_id}")
            
            # 初始化会话状态
            if session_id not in self.user_sessions:
                self.user_sessions[session_id] = {
                    'psql_used': False,
                    'query_count': 0,
                    'last_query_time': None,
                    'database_understood': False,
                    'conversation_history': []
                }
            
            # 记录对话历史
            self.user_sessions[session_id]['conversation_history'].append({
                'role': 'user',
                'content': message,
                'timestamp': datetime.now().isoformat()
            })
            
            # 检查是否包含#psql标记
            has_psql_marker = (
                message_type == 'data_analysis' or 
                '#psql' in message.lower() or 
                '#p s q l' in message.lower()
            )
            
            if has_psql_marker:
                # 标记用户已使用过psql
                self.user_sessions[session_id]['psql_used'] = True
                self.user_sessions[session_id]['query_count'] += 1
                self.user_sessions[session_id]['last_query_time'] = datetime.now()
                
                # 检查是否需要数据库认知流程
                needs_database_intro = self.check_if_needs_database_intro(message, session_id)
                if needs_database_intro:
                    response_data = self.handle_database_introduction(message, session_id)
                else:
                    response_data = self.handle_intelligent_data_analysis(message, session_id)
            else:
                response_data = self.handle_normal_chat(message)
            
            # 记录助手响应
            if response_data.get('status') == 'success':
                self.user_sessions[session_id]['conversation_history'].append({
                    'role': 'assistant',
                    'content': response_data.get('message', ''),
                    'timestamp': datetime.now().isoformat()
                })
            
            # 确保响应格式统一
            return self.ensure_response_format(response_data)
            
        except Exception as e:
            logger.error(f"消息处理失败: {e}")
            logger.error(traceback.format_exc())
            return self.error_response(f"处理消息时发生错误: {str(e)}")

    def check_if_needs_database_intro(self, message, session_id):
        """检查是否需要数据库介绍流程"""
        session = self.user_sessions.get(session_id, {})
        
        # 如果数据库已经理解过，直接进入数据分析
        if session.get('database_understood', False):
            return False
        
        # 清理消息，只看核心内容
        clean_message = self.clean_psql_marker(message).strip()
        
        # 如果消息是探索性的或者包含介绍关键词，需要数据库介绍
        intro_keywords = ['介绍', '有什么', '哪些表', '数据库', '结构', '样本', '示例']
        is_exploratory = (
            len(clean_message) <= 5 or 
            any(keyword in clean_message for keyword in intro_keywords) or
            '?' in clean_message or 
            '？' in clean_message
        )
        
        return is_exploratory

    def handle_database_introduction(self, user_message, session_id):
        """处理数据库介绍流程"""
        try:
            logger.info("🔍 开始数据库介绍流程")
            
            # 从三个表中获取样本数据
            sample_data = self.get_database_samples_detailed()
            if not sample_data:
                return self.error_response_dict("无法获取数据库样本数据")
            
            logger.info(f"获取到样本数据: {[k for k, v in sample_data.items() if v]}")
            
            # 使用AI分析数据库结构
            schema_analysis = self.analyze_database_with_ai(sample_data)
            
            # 生成用户友好的介绍
            user_intro = self.generate_user_friendly_intro(schema_analysis)
            
            # 标记数据库已理解
            self.user_sessions[session_id]['database_understood'] = True
            
            # 格式化响应
            response_html = self.format_database_intro_response(user_intro, sample_data)
            
            return {
                'status': 'success',
                'response_type': 'database_intro', 
                'message': response_html,
                'has_samples': True,
                'database_understood': True
            }
            
        except Exception as e:
            logger.error(f"数据库介绍流程失败: {e}")
            logger.error(traceback.format_exc())
            return self.error_response_dict(f"数据库介绍失败: {str(e)}")

    def get_database_samples_detailed(self):
        """从三个表中获取详细的样本数据"""
        try:
            samples = {}
            tables = ['base_procurement_info_new', 'procurement_intention', 'procurement_notices']
            
            with connection.cursor() as cursor:
                for table in tables:
                    try:
                        # 获取表结构信息
                        cursor.execute(f"""
                            SELECT column_name, data_type, is_nullable 
                            FROM information_schema.columns 
                            WHERE table_name = '{table}' 
                            ORDER BY ordinal_position
                        """)
                        columns_info = cursor.fetchall()
                        
                        # 获取样本数据
                        if table == 'procurement_notices':
                            # 对于公告表，限制content字段长度
                            cursor.execute(f"""
                                SELECT * FROM {table} 
                                WHERE publish_time IS NOT NULL 
                                ORDER BY publish_time DESC 
                                LIMIT 1
                            """)
                        else:
                            cursor.execute(f"""
                                SELECT * FROM {table} 
                                WHERE publish_time IS NOT NULL 
                                ORDER BY publish_time DESC 
                                LIMIT 1
                            """)
                        
                        sample_row = cursor.fetchone()
                        column_names = [col[0] for col in cursor.description]
                        
                        if sample_row:
                            # 构建样本数据字典
                            sample_dict = {}
                            for i, col_name in enumerate(column_names):
                                value = sample_row[i]
                                # 处理长文本字段
                                if col_name == 'content' and value and len(str(value)) > 200:
                                    value = str(value)[:200] + '...'
                                sample_dict[col_name] = value
                            
                            samples[table] = {
                                'structure': [{'name': col[0], 'type': col[1], 'nullable': col[2]} for col in columns_info],
                                'sample': sample_dict
                            }
                        else:
                            samples[table] = None
                            logger.warning(f"表 {table} 中没有数据")
                            
                    except Exception as e:
                        logger.error(f"获取表 {table} 样本失败: {e}")
                        samples[table] = None
            
            return samples
            
        except Exception as e:
            logger.error(f"获取数据库样本失败: {e}")
            return None

    def analyze_database_with_ai(self, sample_data):
        """使用AI分析数据库结构"""
        if not self.ai_client:
            return self.analyze_database_locally(sample_data)
        
        try:
            # 准备样本数据描述
            sample_description = ""
            for table_name, table_data in sample_data.items():
                if table_data:
                    sample_description += f"\n\n{table_name} 表示例:\n"
                    sample_description += f"字段结构: {[col['name'] for col in table_data['structure']]}\n"
                    sample_description += f"样本数据: {json.dumps(table_data['sample'], ensure_ascii=False, default=str)}"
            
            prompt = f"""
请分析以下政府采购数据库的结构和内容：

这是一个政府采购信息数据库，包含三个核心数据表：

1. base_procurement_info_new - 基础采购信息表
2. procurement_intention - 采购意向表  
3. procurement_notices - 采购公告表

各表的样本数据和结构如下：
{sample_description}

请详细分析：
1. 每个表的主要功能和作用
2. 关键字段的含义和用途
3. 表之间的关系和关联方式
4. 数据的业务价值和典型使用场景
5. 用户可以查询哪些类型的信息

请用清晰的中文进行分析，并给出具体的使用示例。
"""
            
            response = self.ai_client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"AI数据库分析失败: {e}")
            return self.analyze_database_locally(sample_data)

    def analyze_database_locally(self, sample_data):
        """本地数据库分析"""
        analysis = """
## 数据库结构分析

### 1. 基础采购信息表 (base_procurement_info_new)
- **功能**: 存储采购项目的基础核心信息
- **关键字段**: 
  - url: 唯一标识符，用于关联其他表
  - title: 采购项目标题
  - jurisdiction: 管辖区域
  - info_type: 信息类型（招标公告、中标公示等）
  - publish_time: 发布时间

### 2. 采购意向表 (procurement_intention)  
- **功能**: 存储采购意向和预算信息
- **关键字段**:
  - intention_budget_amount: 预算金额
  - intention_procurement_unit: 采购单位
  - intention_project_name: 项目名称

### 3. 采购公告表 (procurement_notices)
- **功能**: 存储完整的采购公告内容
- **关键字段**:
  - content: 详细的公告内容（JSON格式）

### 表关系
- 三个表通过 `url` 字段进行关联
- base_procurement_info_new 是核心表，其他表通过url与之关联

### 典型查询示例
- "查询北京市最近的医疗设备采购"
- "统计2024年各地区的采购预算"
- "显示教育局的招标公告"
- "分析医疗行业的采购趋势"
"""
        return analysis

    def generate_user_friendly_intro(self, schema_analysis):
        """生成用户友好的介绍"""
        if not self.ai_client:
            return self.generate_intro_locally(schema_analysis)
        
        try:
            prompt = f"""
基于以下数据库分析，生成一段对普通用户友好的介绍：

{schema_analysis}

要求：
1. 用通俗易懂的中文介绍数据库
2. 说明可以查询哪些信息
3. 给出具体的查询示例
4. 语气友好、有帮助性

请直接返回介绍文字。
"""
            
            response = self.ai_client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"AI介绍生成失败: {e}")
            return self.generate_intro_locally(schema_analysis)

    def generate_intro_locally(self, schema_analysis):
        """生成本地介绍"""
        return """
## 🏛️ 政府采购数据库介绍

我已成功连接到政府采购数据库，这里有丰富的采购信息供您查询：

### 📊 数据库包含什么？
- **基础采购信息**: 项目标题、地区、采购类型、发布时间等
- **采购意向**: 预算金额、采购单位、项目详情  
- **采购公告**: 完整的公告文本和详细内容

### 🔍 您可以查询什么？
- 特定地区的采购项目（如：北京、上海）
- 各类采购类型（招标公告、中标公示、采购意向）
- 预算金额分析和统计
- 时间范围内的采购动态

### 💡 查询示例
- "显示北京市最近的医疗设备采购"
- "查询教育局2024年采购预算"  
- "统计11月份招标公告数量"
- "分析医疗行业的采购趋势"

请告诉我您想了解什么信息，我会为您生成详细的数据分析报告！
"""

    def format_database_intro_response(self, introduction, sample_data):
        """格式化数据库介绍响应"""
        html_parts = []
        
        html_parts.append("""
        <div class="database-intro-container">
            <div class="alert alert-info mb-4">
                <div class="d-flex align-items-center mb-3">
                    <span class="fs-4 me-2">🎯</span>
                    <h4 class="mb-0">数据库认知完成</h4>
                </div>
        """)
        
        # 添加介绍内容
        html_parts.append(f'<div class="intro-content">{introduction}</div>')
        
        html_parts.append("""
            </div>
            
            <div class="sample-preview">
                <h5 class="mb-3">📋 数据样本预览</h5>
                <div class="row g-3">
        """)
        
        # 添加样本数据预览
        for table_name, table_data in sample_data.items():
            if table_data and table_data.get('sample'):
                sample = table_data['sample']
                html_parts.append(f"""
                    <div class="col-md-6 col-lg-4">
                        <div class="card h-100">
                            <div class="card-header bg-primary text-white">
                                <strong>{self.format_table_name(table_name)}</strong>
                            </div>
                            <div class="card-body">
                                {self.format_sample_preview(sample)}
                            </div>
                        </div>
                    </div>
                """)
        
        html_parts.append("""
                </div>
            </div>
            
            <div class="mt-4 alert alert-success">
                <strong>💡 提示:</strong> 现在您可以提出具体的数据查询需求了！
                例如："查询11月医疗行业的采购意向" 或 "显示最近的招标公告"
            </div>
        </div>
        """)
        
        return "".join(html_parts)

    def format_table_name(self, table_name):
        """格式化表名显示"""
        name_map = {
            'base_procurement_info_new': '基础采购信息',
            'procurement_intention': '采购意向', 
            'procurement_notices': '采购公告'
        }
        return name_map.get(table_name, table_name)

    def format_sample_preview(self, sample):
        """格式化样本数据预览"""
        preview_html = []
        key_fields = ['title', 'jurisdiction', 'info_type', 'publish_time', 
                     'intention_budget_amount', 'intention_procurement_unit']
        
        for field in key_fields:
            if field in sample and sample[field]:
                value = sample[field]
                display_value = str(value)
                if len(display_value) > 30:
                    display_value = display_value[:30] + '...'
                
                field_name = self.format_header_name(field)
                preview_html.append(f"""
                    <div class="mb-2">
                        <small><strong>{field_name}:</strong> {display_value}</small>
                    </div>
                """)
        
        return "".join(preview_html)

    def handle_intelligent_data_analysis(self, user_message, session_id):
        """智能数据分析处理 - 深度理解、内容提取、智能回答"""
        try:
            # 清理消息
            clean_message = self.clean_psql_marker(user_message)
            logger.info(f"开始智能数据分析: {clean_message}")
            
            # 获取对话历史
            conversation_history = self.user_sessions[session_id].get('conversation_history', [])
            
            # 深度理解用户意图
            intent_analysis = self.analyze_user_intent(clean_message)
            
            # 根据意图选择查询策略
            if self.requires_content_analysis(intent_analysis):
                return self.handle_intelligent_content_analysis(clean_message, intent_analysis, session_id, conversation_history)
            else:
                return self.handle_basic_data_query(clean_message, intent_analysis, session_id)
                
        except Exception as e:
            logger.error(f"智能数据分析处理失败: {e}")
            logger.error(traceback.format_exc())
            return self.error_response_dict(f"数据分析失败: {str(e)}")

    def analyze_user_intent(self, user_message):
        """深度分析用户意图"""
        medical_keywords = ['医疗', '医院', '药品', '器械', '保健', '卫生', '医学', '医保', '诊疗']
        intention_keywords = ['意向', '采购意向', '预算']
        notice_keywords = ['公告', '招标', '中标', '要求', '资质', '联系人', '内容']
        
        intent = {
            'industry': '医疗' if any(kw in user_message for kw in medical_keywords) else '通用',
            'query_type': '意向' if any(kw in user_message for kw in intention_keywords) else 
                         '公告' if any(kw in user_message for kw in notice_keywords) else '通用',
            'time_range': '11月' if '11月' in user_message or '十一月' in user_message else 
                         '近期' if '最近' in user_message or '最新' in user_message else '',
            'needs_contact': '联系人' in user_message or '联系' in user_message or '电话' in user_message,
            'needs_qualification': '资质' in user_message or '要求' in user_message or '条件' in user_message,
            'needs_content': '内容' in user_message or '详情' in user_message or '要求' in user_message,
            'needs_url': '网址' in user_message or '链接' in user_message
        }
        
        logger.info(f"用户意图分析: {intent}")
        return intent

    def requires_content_analysis(self, intent_analysis):
        """判断是否需要内容分析"""
        return (intent_analysis['needs_contact'] or 
                intent_analysis['needs_qualification'] or 
                intent_analysis['needs_content'] or
                intent_analysis['query_type'] == '公告')

    def handle_intelligent_content_analysis(self, user_message, intent_analysis, session_id, conversation_history):
        """处理智能内容分析"""
        try:
            # 获取相关数据（包含content字段）
            raw_data = self.get_content_rich_data(intent_analysis)
            
            if not raw_data:
                return self.format_no_data_response(user_message)
            
            # 深度分析content内容
            analyzed_results = self.analyze_content_data(raw_data, intent_analysis)
            
            # 生成智能回答
            intelligent_response = self.generate_intelligent_response(
                user_message, analyzed_results, intent_analysis, conversation_history
            )
            
            response_data = {
                'status': 'success',
                'response_type': 'intelligent_analysis',
                'message': intelligent_response,
                'data_count': len(raw_data),
                'analysis_depth': 'deep',
                'formatted': True
            }
            
            logger.info(f"智能分析完成，返回 {len(raw_data)} 条数据的分析结果")
            return response_data
            
        except Exception as e:
            logger.error(f"智能内容分析失败: {e}")
            # 降级处理
            return self.handle_basic_data_query(user_message, intent_analysis, session_id)

    def get_content_rich_data(self, intent_analysis):
        """获取包含content字段的详细数据"""
        try:
            base_query = """
            SELECT 
                base.url, base.title, base.jurisdiction, base.info_type, base.publish_time,
                notices.content as notice_content,
                intention.intention_budget_amount, intention.intention_procurement_unit,
                intention.intention_project_name
            FROM base_procurement_info_new base
            LEFT JOIN procurement_notices notices ON base.url = notices.url
            LEFT JOIN procurement_intention intention ON base.url = intention.url
            WHERE 1=1
            """
            
            conditions = self.build_intelligent_conditions(intent_analysis)
            
            if conditions:
                base_query += " AND " + " AND ".join(conditions)
            
            base_query += " ORDER BY base.publish_time DESC LIMIT 100"
            
            logger.info(f"智能查询SQL: {base_query}")
            
            with connection.cursor() as cursor:
                cursor.execute(base_query)
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                
                results = []
                for row in rows:
                    row_dict = {}
                    for i, col in enumerate(columns):
                        # 特别处理content字段
                        if col == 'notice_content' and row[i]:
                            try:
                                # 尝试解析JSON格式的content
                                if isinstance(row[i], str) and row[i].strip().startswith('{'):
                                    content_data = json.loads(row[i])
                                    row_dict[col] = content_data
                                else:
                                    row_dict[col] = str(row[i])
                            except:
                                # 解析失败，使用原文本
                                row_dict[col] = str(row[i])
                        else:
                            row_dict[col] = row[i]
                    results.append(row_dict)
                
                return results
                
        except Exception as e:
            logger.error(f"获取详细数据失败: {e}")
            return None

    def build_intelligent_conditions(self, intent_analysis):
        """构建智能查询条件"""
        conditions = []
        
        # 行业条件
        if intent_analysis['industry'] == '医疗':
            medical_keywords = ['医疗', '医院', '药品', '器械', '保健', '卫生', '医学', '医保']
            medical_conds = [f"base.title LIKE '%{kw}%'" for kw in medical_keywords]
            conditions.append("(" + " OR ".join(medical_conds) + ")")
        
        # 时间条件
        if intent_analysis['time_range'] == '11月':
            current_year = datetime.now().year
            conditions.append(f"EXTRACT(MONTH FROM base.publish_time) = 11")
            conditions.append(f"EXTRACT(YEAR FROM base.publish_time) = {current_year}")
        elif intent_analysis['time_range'] == '近期':
            conditions.append(f"base.publish_time >= CURRENT_DATE - INTERVAL '30 days'")
        
        # 类型条件
        if intent_analysis['query_type'] == '意向':
            conditions.append("base.info_type LIKE '%意向%'")
        elif intent_analysis['query_type'] == '公告':
            conditions.append("(base.info_type LIKE '%公告%' OR base.info_type LIKE '%招标%' OR base.info_type LIKE '%中标%')")
        
        # 确保只查询有效数据
        conditions.append("base.publish_time IS NOT NULL")
        conditions.append("base.title IS NOT NULL")
        
        return conditions

    def analyze_content_data(self, raw_data, intent_analysis):
        """深度分析内容数据"""
        analyzed_results = []
        
        for item in raw_data:
            analysis = {
                'title': item.get('title', ''),
                'url': item.get('url', ''),
                'publish_time': item.get('publish_time', ''),
                'jurisdiction': item.get('jurisdiction', ''),
                'info_type': item.get('info_type', ''),
                'budget': item.get('intention_budget_amount'),
                'procurement_unit': item.get('intention_procurement_unit'),
                'project_name': item.get('intention_project_name'),
                'extracted_info': {}
            }
            
            # 从content中提取关键信息
            content = item.get('notice_content', '')
            if content:
                # 提取文本内容
                content_text = self.extract_text_from_content(content)
                
                # 提取联系人信息
                if intent_analysis['needs_contact']:
                    analysis['extracted_info']['contact'] = self.extract_contact_info(content_text)
                
                # 提取资质要求
                if intent_analysis['needs_qualification']:
                    analysis['extracted_info']['qualifications'] = self.extract_qualification_info(content_text)
                
                # 提取其他关键信息
                analysis['extracted_info']['key_points'] = self.extract_key_points(content_text, intent_analysis)
                
                # 提取主要内容摘要
                analysis['extracted_info']['content_summary'] = self.extract_content_summary(content_text)
            
            analyzed_results.append(analysis)
        
        return analyzed_results

    def extract_text_from_content(self, content):
        """从content中提取文本"""
        if isinstance(content, str):
            return content
        elif isinstance(content, dict):
            # 从字典中提取文本内容
            text_parts = []
            for key, value in content.items():
                if isinstance(value, str) and len(value.strip()) > 10:
                    text_parts.append(value.strip())
                elif isinstance(value, (list, dict)):
                    # 递归处理嵌套结构
                    try:
                        nested_text = json.dumps(value, ensure_ascii=False)
                        if len(nested_text) > 20:
                            text_parts.append(nested_text)
                    except:
                        pass
            return " ".join(text_parts)
        else:
            return str(content)

    def extract_contact_info(self, text):
        """提取联系人信息"""
        contact_info = {}
        
        # 联系人姓名
        name_patterns = [
            r'联系人[：:]\s*([^\s，。]{2,10}?)(?=[，。\s]|$)',
            r'联系人员[：:]\s*([^\s，。]{2,10}?)(?=[，。\s]|$)',
            r'项目联系人[：:]\s*([^\s，。]{2,10}?)(?=[，。\s]|$)',
            r'联系人姓名[：:]\s*([^\s，。]{2,10}?)(?=[，。\s]|$)'
        ]
        
        for pattern in name_patterns:
            matches = re.findall(pattern, text)
            if matches:
                contact_info['person'] = matches[0].strip()
                break
        
        # 联系电话
        phone_patterns = [
            r'电话[：:]\s*([0-9-()（）]{7,15}?)(?=[，。\s]|$)',
            r'联系电话[：:]\s*([0-9-()（）]{7,15}?)(?=[，。\s]|$)',
            r'联系方式[：:]\s*([0-9-()（）]{7,15}?)(?=[，。\s]|$)',
            r'手机[：:]\s*([0-9-()（）]{7,15}?)(?=[，。\s]|$)'
        ]
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            if matches:
                contact_info['phone'] = matches[0].strip()
                break
        
        return contact_info if contact_info else {"info": "详见公告内容"}

    def extract_qualification_info(self, text):
        """提取资质要求信息"""
        qualifications = []
        
        # 资质要求段落提取
        qual_patterns = [
            r'资质要求[：:](.*?)(?=投标人资格|申请人资格|资格条件|$)',
            r'投标人资格[：:](.*?)(?=资质要求|申请人资格|资格条件|$)',
            r'申请人资格[：:](.*?)(?=资质要求|投标人资格|资格条件|$)',
            r'资格条件[：:](.*?)(?=资质要求|投标人资格|申请人资格|$)'
        ]
        
        for pattern in qual_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                # 清理匹配结果
                cleaned = match.strip()
                if len(cleaned) > 10:  # 确保有实际内容
                    qualifications.append(cleaned)
        
        # 如果没找到完整段落，提取关键词周围的句子
        if not qualifications:
            qual_keywords = ['资质', '资格', '要求', '条件', '具备']
            sentences = re.split(r'[。！？]', text)
            for sentence in sentences:
                if any(keyword in sentence for keyword in qual_keywords) and len(sentence) > 15:
                    qualifications.append(sentence.strip())
        
        return qualifications[:3] if qualifications else ["具体资质要求请查看完整公告内容"]

    def extract_key_points(self, text, intent_analysis):
        """提取关键信息点"""
        key_points = []
        
        # 根据用户意图提取相关信息
        if intent_analysis['industry'] == '医疗':
            medical_terms = ['医疗设备', '医疗器械', '药品', '医疗服务', '医疗技术', '医院', '卫生']
            for term in medical_terms:
                if term in text:
                    key_points.append(f"涉及{term}采购")
        
        # 提取时间信息
        time_patterns = [
            r'投标截止[时间]*[：:]\s*([^，。]{10,30}?)(?=[，。\s]|$)',
            r'开标时间[：:]\s*([^，。]{10,30}?)(?=[，。\s]|$)',
            r'报名时间[：:]\s*([^，。]{10,30}?)(?=[，。\s]|$)'
        ]
        
        for pattern in time_patterns:
            matches = re.findall(pattern, text)
            if matches:
                key_points.append(f"重要时间: {matches[0]}")
        
        # 提取预算信息
        if '预算' in text or '金额' in text:
            budget_patterns = [
                r'预算[金额]*[：:]\s*([^，。]{5,20}?)(?=[，。\s]|$)',
                r'项目金额[：:]\s*([^，。]{5,20}?)(?=[，。\s]|$)'
            ]
            for pattern in budget_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    key_points.append(f"预算信息: {matches[0]}")
        
        return key_points[:5]  # 最多返回5个关键点

    def extract_content_summary(self, text):
        """提取内容摘要"""
        # 取前200个字符作为摘要
        if len(text) > 200:
            return text[:200] + "..."
        return text

    def generate_intelligent_response(self, user_message, analyzed_results, intent_analysis, conversation_history):
        """生成智能回答"""
        if not analyzed_results:
            return self.format_no_data_response(user_message)
        
        # 使用AI生成智能回答（如果有AI客户端）
        if self.ai_client:
            try:
                return self.generate_ai_enhanced_response(user_message, analyzed_results, intent_analysis, conversation_history)
            except Exception as e:
                logger.error(f"AI增强回答生成失败: {e}")
        
        # 降级到模板回答
        return self.generate_template_response(user_message, analyzed_results, intent_analysis)

    def generate_ai_enhanced_response(self, user_message, analyzed_results, intent_analysis, conversation_history):
        """使用AI生成增强回答"""
        # 准备数据摘要
        data_summary = self.prepare_data_summary_for_ai(analyzed_results)
        
        # 准备对话历史上下文
        history_context = self.prepare_conversation_history(conversation_history[-4:])  # 最近2轮对话
        
        prompt = f"""
作为政府采购数据分析专家，请基于以下数据回答用户的问题。

用户当前问题：{user_message}

对话历史上下文：
{history_context}

查询到的数据摘要（共{len(analyzed_results)}条记录）：
{data_summary}

用户关注的重点：
- 行业领域：{intent_analysis['industry']}
- 查询类型：{intent_analysis['query_type']}
- 时间范围：{intent_analysis['time_range']}
- 需要联系人信息：{'是' if intent_analysis['needs_contact'] else '否'}
- 需要资质要求：{'是' if intent_analysis['needs_qualification'] else '否'}

回答要求：
1. 直接、准确地回答用户问题，不要提及SQL或技术细节
2. 基于实际数据引用具体信息（标题、预算、联系人等）
3. 对信息进行总结分析，提供业务洞察
4. 使用专业但易懂的中文，结构清晰
5. 对于资质要求、联系人等详细信息，要具体引用内容
6. 如果数据较多，进行分类总结

请生成专业、有用的回答：
"""
        
        response = self.ai_client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.3
        )
        
        return f"""
        <div class="intelligent-analysis-result">
            <div class="alert alert-success">
                <h4>🧠 智能分析结果</h4>
                <p><strong>您的查询：</strong> {user_message}</p>
            </div>
            <div class="analysis-content">
                {response.choices[0].message.content}
            </div>
            <div class="mt-3 alert alert-info">
                <small>📊 基于 {len(analyzed_results)} 条相关数据进行的深度分析</small>
            </div>
        </div>
        """

    def prepare_data_summary_for_ai(self, analyzed_results):
        """为AI准备数据摘要"""
        if not analyzed_results:
            return "未找到相关数据"
        
        summary = f"共找到 {len(analyzed_results)} 条相关记录：\n\n"
        
        for i, result in enumerate(analyzed_results[:10], 1):  # 最多10条
            summary += f"{i}. {result.get('title', '无标题')}\n"
            summary += f"   地区：{result.get('jurisdiction', '未知')} | 类型：{result.get('info_type', '未知')}\n"
            summary += f"   时间：{result.get('publish_time', '未知')}\n"
            
            if result.get('budget'):
                summary += f"   预算：{result.get('budget')}元\n"
            
            # 联系人信息
            if result['extracted_info'].get('contact'):
                contact = result['extracted_info']['contact']
                if contact.get('person'):
                    summary += f"   联系人：{contact['person']}"
                    if contact.get('phone'):
                        summary += f" | 电话：{contact['phone']}"
                    summary += "\n"
            
            # 资质要求
            if result['extracted_info'].get('qualifications'):
                quals = result['extracted_info']['qualifications']
                summary += f"   资质要求：{quals[0][:50]}...\n"
            
            summary += "\n"
        
        if len(analyzed_results) > 10:
            summary += f"... 还有 {len(analyzed_results) - 10} 条记录\n"
        
        return summary

    def prepare_conversation_history(self, history):
        """准备对话历史"""
        if not history:
            return "无历史对话"
        
        formatted = []
        for msg in history:
            role = "用户" if msg['role'] == 'user' else "助手"
            # 截断过长的消息
            content = msg['content']
            if len(content) > 100:
                content = content[:100] + "..."
            formatted.append(f"{role}: {content}")
        
        return "\n".join(formatted)

    def generate_template_response(self, user_message, analyzed_results, intent_analysis):
        """生成模板回答"""
        if not analyzed_results:
            return self.format_no_data_response(user_message)
        
        html_parts = []
        
        html_parts.append(f"""
        <div class="intelligent-analysis-result">
            <div class="alert alert-success">
                <h4>📊 智能分析结果</h4>
                <p><strong>您的查询：</strong> {user_message}</p>
                <p><strong>找到相关项目：</strong> {len(analyzed_results)} 个</p>
            </div>
        """)
        
        # 按类型分组显示
        grouped_results = {}
        for result in analyzed_results:
            info_type = result.get('info_type', '其他')
            if info_type not in grouped_results:
                grouped_results[info_type] = []
            grouped_results[info_type].append(result)
        
        for info_type, items in grouped_results.items():
            html_parts.append(f"""
            <div class="mb-4">
                <h5>{info_type} ({len(items)}个)</h5>
            """)
            
            for i, item in enumerate(items[:5], 1):  # 每组最多显示5个
                html_parts.append(self.format_single_item_html(item, i))
            
            if len(items) > 5:
                html_parts.append(f'<p class="text-muted">... 还有 {len(items) - 5} 个{info_type}项目</p>')
            
            html_parts.append("</div>")
        
        html_parts.append("</div>")
        return "".join(html_parts)

    def format_single_item_html(self, item, index):
        """格式化单个项目显示"""
        html = f"""
        <div class="card mb-3">
            <div class="card-body">
                <h6 class="card-title">{index}. {item.get('title', '无标题')}</h6>
                <div class="row">
                    <div class="col-md-6">
                        <small><strong>地区：</strong>{item.get('jurisdiction', '未知')}</small><br>
                        <small><strong>时间：</strong>{item.get('publish_time', '未知')}</small>
                    </div>
                    <div class="col-md-6">
        """
        
        if item.get('budget'):
            html += f'<small><strong>预算：</strong>¥{item.get("budget"):,.2f}</small><br>'
        
        if item.get('procurement_unit'):
            html += f'<small><strong>采购单位：</strong>{item.get("procurement_unit")}</small>'
        
        html += """
                    </div>
                </div>
        """
        
        # 显示提取的信息
        if item['extracted_info'].get('contact'):
            contact = item['extracted_info']['contact']
            if contact.get('person') or contact.get('phone'):
                html += '<div class="mt-2"><small><strong>📞 联系方式：</strong>'
                if contact.get('person'):
                    html += f'{contact["person"]} '
                if contact.get('phone'):
                    html += f'{contact["phone"]}'
                html += '</small></div>'
        
        if item['extracted_info'].get('qualifications'):
            quals = item['extracted_info']['qualifications']
            html += f'<div class="mt-1"><small><strong>📋 资质要求：</strong>{quals[0][:80]}...</small></div>'
        
        if item.get('url'):
            html += f'<div class="mt-2"><a href="{item["url"]}" target="_blank" class="btn btn-sm btn-outline-primary">查看详细公告</a></div>'
        
        html += """
            </div>
        </div>
        """
        return html

    def format_no_data_response(self, user_message):
        """格式化无数据响应"""
        return f"""
        <div class="alert alert-warning">
            <h4>🔍 查询结果</h4>
            <p>未找到与 "<strong>{user_message}</strong>" 相关的采购信息。</p>
            <p>建议：</p>
            <ul>
                <li>检查查询条件是否过于具体</li>
                <li>尝试更广泛的关键词搜索</li>
                <li>确认时间范围是否合适</li>
            </ul>
        </div>
        """

    def handle_basic_data_query(self, user_message, intent_analysis, session_id):
        """处理基础数据查询（兼容原有逻辑）"""
        try:
            # 原有的简单查询逻辑
            target_tables = self.select_target_tables(user_message)
            sql_query = self.generate_sql_query(user_message, target_tables)
            
            if not sql_query:
                return self.error_response_dict("无法生成有效的SQL查询")
            
            query_result = self.execute_sql_query(sql_query)
            if query_result is None:
                return self.error_response_dict("数据库查询失败")
            
            analysis_result = self.analyze_query_results(user_message, query_result, target_tables)
            final_response = self.format_data_analysis_response(
                user_message, sql_query, query_result, analysis_result, target_tables
            )
            
            return final_response
            
        except Exception as e:
            logger.error(f"基础数据查询失败: {e}")
            return self.error_response_dict(f"查询失败: {str(e)}")

    # 保留原有的兼容性方法
    def select_target_tables(self, user_message):
        """选择目标表"""
        message_lower = user_message.lower()
        
        if '意向' in message_lower or '预算' in message_lower:
            return 'procurement_intention'
        elif '公告' in message_lower or '内容' in message_lower:
            return 'procurement_notices'
        else:
            return 'base_procurement_info_new'

    def generate_sql_query(self, natural_language_query, target_tables):
        """生成SQL查询"""
        query_lower = natural_language_query.lower()
        
        # 构建基础查询
        if isinstance(target_tables, list):
            base_sql = """
            SELECT 
                base.url, base.title, base.jurisdiction, base.info_type, base.publish_time,
                intention.intention_budget_amount, intention.intention_procurement_unit
            FROM base_procurement_info_new base
            LEFT JOIN procurement_intention intention ON base.url = intention.url
            WHERE 1=1
            """
        else:
            if target_tables == 'procurement_intention':
                base_sql = """
                SELECT url, title, jurisdiction, info_type, publish_time, 
                       intention_budget_amount, intention_procurement_unit 
                FROM procurement_intention WHERE 1=1
                """
            elif target_tables == 'procurement_notices':
                base_sql = """
                SELECT url, title, jurisdiction, info_type, publish_time, 
                       LEFT(content::text, 200) as content_preview
                FROM procurement_notices WHERE 1=1
                """
            else:
                base_sql = "SELECT url, title, jurisdiction, info_type, publish_time FROM base_procurement_info_new WHERE 1=1"
        
        # 添加条件
        conditions = self.build_sql_conditions(query_lower, target_tables)
        
        if conditions:
            base_sql += " AND " + " AND ".join(conditions)
        
        # 添加排序
        base_sql = self.add_ordering(base_sql, query_lower, target_tables)
        
        # 限制结果数量
        base_sql += " LIMIT 100"
        
        return base_sql

    def build_sql_conditions(self, query_lower, target_table):
        """构建SQL条件"""
        conditions = []
        
        # 医疗行业关键词
        medical_keywords = ['医疗', '医院', '药品', '器械', '保健', '卫生', '医学', '医保', '诊疗', '卫生院']
        medical_matches = [kw for kw in medical_keywords if kw in query_lower]
        if medical_matches:
            medical_conditions = [f"title LIKE '%{kw}%'" for kw in medical_matches]
            conditions.append("(" + " OR ".join(medical_conditions) + ")")
        
        # 采购意向筛选
        if '意向' in query_lower or '采购意向' in query_lower:
            conditions.append("info_type LIKE '%意向%'")
        
        # 11月时间筛选
        if '11月' in query_lower or '十一月' in query_lower:
            conditions.append("EXTRACT(MONTH FROM publish_time) = 11")
            current_year = datetime.now().year
            conditions.append(f"EXTRACT(YEAR FROM publish_time) = {current_year}")
        
        # 其他条件
        if '招标' in query_lower:
            conditions.append("info_type LIKE '%招标%'")
        elif '中标' in query_lower:
            conditions.append("info_type LIKE '%中标%'")
        
        return conditions

    def add_ordering(self, base_sql, query_lower, target_table):
        """添加排序"""
        if '最新' in query_lower or '最近' in query_lower:
            base_sql += " ORDER BY publish_time DESC"
        elif '预算' in query_lower and target_table == 'procurement_intention':
            base_sql += " ORDER BY intention_budget_amount DESC"
        else:
            base_sql += " ORDER BY publish_time DESC"
        
        return base_sql

    def analyze_query_results(self, original_query, query_results, target_tables):
        """分析查询结果"""
        if not query_results:
            return "未找到匹配的数据"
        
        try:
            analysis_parts = []
            analysis_parts.append(f"共找到 {len(query_results)} 条相关记录")
            
            # 时间分析
            if query_results and 'publish_time' in query_results[0]:
                dates = [r['publish_time'] for r in query_results if r.get('publish_time')]
                if dates:
                    latest = max(dates)
                    oldest = min(dates)
                    analysis_parts.append(f"时间范围: {oldest} 至 {latest}")
            
            # 地区分布
            if query_results and 'jurisdiction' in query_results[0]:
                jurisdictions = [r['jurisdiction'] for r in query_results if r.get('jurisdiction')]
                if jurisdictions:
                    jurisdiction_counts = Counter(jurisdictions)
                    top_areas = jurisdiction_counts.most_common(3)
                    area_info = ", ".join([f"{area}({count})" for area, count in top_areas])
                    analysis_parts.append(f"主要地区: {area_info}")
            
            # 预算分析
            if query_results and 'intention_budget_amount' in query_results[0]:
                budgets = [r['intention_budget_amount'] for r in query_results if r.get('intention_budget_amount')]
                if budgets:
                    valid_budgets = [b for b in budgets if b and b > 0]
                    if valid_budgets:
                        total_budget = sum(valid_budgets)
                        avg_budget = total_budget / len(valid_budgets)
                        analysis_parts.append(f"平均预算: ¥{avg_budget:,.2f}")
            
            return " | ".join(analysis_parts)
            
        except Exception as e:
            logger.error(f"结果分析失败: {e}")
            return "数据分析完成"

    def format_data_analysis_response(self, original_query, sql_query, query_results, analysis, target_tables):
        """格式化数据分析响应"""
        # 生成HTML格式的响应
        html_response = self.generate_html_analysis(original_query, sql_query, query_results, analysis, target_tables)
        
        return {
            'status': 'success',
            'response_type': 'data_analysis',
            'message': html_response,
            'data_count': len(query_results),
            'sql_query': sql_query,
            'analysis_summary': analysis,
            'table_used': target_tables,
            'formatted': True
        }

    def generate_html_analysis(self, original_query, sql_query, query_results, analysis, target_tables):
        """生成HTML格式的分析报告"""
        if not query_results:
            return f"""
            <div class="alert alert-warning">
                <h4>🔍 查询结果</h4>
                <p>未找到匹配的数据，请尝试调整搜索条件。</p>
                <p><strong>原始查询:</strong> {original_query}</p>
            </div>
            """
        
        html_parts = []
        
        # 头部信息
        html_parts.append(f"""
        <div class="data-analysis-result">
            <div class="analysis-header alert alert-success">
                <h4>📊 数据分析结果</h4>
                <p><strong>查询:</strong> {original_query}</p>
                <p><strong>结果:</strong> {analysis}</p>
                <p><strong>数据表:</strong> {target_tables}</p>
            </div>
        """)
        
        # SQL查询预览
        if sql_query:
            html_parts.append(f"""
            <div class="sql-preview mb-3">
                <details>
                    <summary class="btn btn-outline-secondary btn-sm">🔍 查看SQL查询</summary>
                    <pre class="mt-2 p-3 bg-light border rounded"><code>{sql_query}</code></pre>
                </details>
            </div>
            """)
        
        # 数据表格
        html_parts.append(self.generate_data_table_html(query_results))
        
        html_parts.append("</div>")
        return "".join(html_parts)

    def generate_data_table_html(self, data):
        """生成数据表格HTML"""
        if not data:
            return '<div class="alert alert-warning">暂无数据</div>'
        
        headers = list(data[0].keys())
        
        table_html = f"""
        <div class="table-responsive mt-3">
            <table class="table table-hover table-striped">
                <thead class="table-dark">
                    <tr>{"".join([f"<th>{self.format_header_name(h)}</th>" for h in headers])}</tr>
                </thead>
                <tbody>
        """
        
        for row in data[:1000]:
            table_html += "<tr>"
            for header in headers:
                value = row.get(header, '')
                table_html += f"<td>{self.format_cell_value(value, header)}</td>"
            table_html += "</tr>"
        
        table_html += """
                </tbody>
            </table>
        </div>
        """
        
        if len(data) > 1000:
            table_html += f'<div class="mt-2 text-muted">仅显示前1000条记录，共{len(data)}条记录</div>'
        
        return table_html

    def format_header_name(self, header):
        """格式化表头名称"""
        header_map = {
            'url': '🔗 链接',
            'title': '📝 标题',
            'jurisdiction': '📍 地区',
            'info_type': '📊 类型',
            'publish_time': '📅 时间',
            'intention_budget_amount': '💰 预算',
            'intention_procurement_unit': '🏢 采购单位',
            'content_preview': '📄 内容预览'
        }
        return header_map.get(header, header)

    def format_cell_value(self, value, header):
        """格式化单元格值"""
        if value is None or value == '':
            return '<span class="text-muted">-</span>'
        
        if header == 'url' and isinstance(value, str) and value.startswith('http'):
            return f'<a href="{value}" target="_blank" class="text-primary">查看详情</a>'
        
        if header == 'intention_budget_amount' and value:
            if isinstance(value, (int, float)):
                return f'¥{value:,.2f}'
        
        if isinstance(value, str) and len(value) > 50:
            return f'<span title="{value}">{value[:50]}...</span>'
        
        return str(value)

    def get_database_context(self):
        """获取数据库上下文"""
        global database_understanding_cache
        if database_understanding_cache.get('schema_info'):
            return database_understanding_cache['schema_info']
        return None

    def execute_sql_query(self, sql_query):
        """执行SQL查询"""
        try:
            with connection.cursor() as cursor:
                # 安全检查：只允许SELECT查询
                sql_upper = sql_query.upper().strip()
                if not sql_upper.startswith('SELECT'):
                    logger.warning(f"非SELECT查询被拒绝: {sql_query}")
                    return None
                
                cursor.execute(sql_query)
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                
                result = []
                for row in rows:
                    row_dict = {}
                    for i, col in enumerate(columns):
                        value = row[i]
                        if value and columns[i] == 'content' and isinstance(value, str) and value.startswith('{'):
                            try:
                                row_dict[col] = json.loads(value)
                            except:
                                row_dict[col] = value
                        else:
                            row_dict[col] = value
                    result.append(row_dict)
                
                return result
        except Exception as e:
            logger.error(f"SQL执行失败: {e}")
            return None

    def handle_normal_chat(self, message):
        """处理普通聊天"""
        if self.ai_client:
            try:
                response = self.ai_client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": message}],
                    max_tokens=500
                )
                return {
                    'status': 'success',
                    'response_type': 'normal_chat',
                    'message': response.choices[0].message.content
                }
            except Exception as e:
                logger.error(f"AI聊天失败: {e}")
        
        return {
            'status': 'success',
            'response_type': 'normal_chat', 
            'message': '您好！如需数据查询，请在消息中添加 #psql 标签。'
        }

    def clean_psql_marker(self, message):
        """清理消息中的psql标记"""
        markers = ['#psql', '#p s q l', '#PSQL', '#P S Q L']
        cleaned = message
        for marker in markers:
            cleaned = cleaned.replace(marker, '')
        return cleaned.strip()

    def ensure_response_format(self, response_data):
        """确保响应格式统一"""
        if isinstance(response_data, JsonResponse):
            return response_data
        
        if isinstance(response_data, dict):
            if 'status' not in response_data:
                response_data['status'] = 'success'
            if 'timestamp' not in response_data:
                response_data['timestamp'] = datetime.now().isoformat()
            
            return JsonResponse(response_data)
        else:
            return self.error_response("服务器返回了未知的响应格式")

    def error_response_dict(self, error_message):
        """返回错误响应的字典格式"""
        return {
            'status': 'error',
            'message': error_message
        }

    def error_response(self, error_message):
        """返回错误响应的JsonResponse格式"""
        return JsonResponse({
            'status': 'error',
            'message': error_message,
            'timestamp': datetime.now().isoformat()
        })

# 创建全局处理器实例
chat_processor = ChatMessageProcessor()

@csrf_exempt
@require_http_methods(["GET", "POST"])
def chat(request):
    """统一的chat视图"""
    
    if request.method == 'GET':
        return render(request, 'tool/chat.html')
    
    elif request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST
            
            if 'session_id' not in data:
                data['session_id'] = 'default'
            
            return chat_processor.process_message(data)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error', 
                'message': '数据格式错误'
            }, status=400)
        except Exception as e:
            logger.error(f"服务器内部错误: {e}")
            return JsonResponse({
                'status': 'error', 
                'message': f'服务器内部错误: {str(e)}'
            }, status=500)
