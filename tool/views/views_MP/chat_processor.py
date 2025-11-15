# tool/views/views_MP/chat_processor.py
import os
import json
import logging
import re
import traceback
from collections import Counter
from datetime import datetime
from django.db import connection
from django.conf import settings

# 配置详细的日志记录
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ChatMessageProcessor:
    """聊天消息处理器 - 增加详细日志"""
    
    def __init__(self):
        self.ai_client = None
        self.setup_ai_client()
        self.user_sessions = {}
        self.session_data_cache = {}
        
        # 确保保存目录存在
        try:
            save_dir = "D:/code/localtxt"
            os.makedirs(save_dir, exist_ok=True)
            logger.info(f"📁 确保保存目录存在: {save_dir}")
        except Exception as e:
            logger.error(f"❌ 创建保存目录失败: {e}")
        
        logger.info("ChatMessageProcessor 初始化完成")

    # 添加缺失的 error_response 方法
    def error_response(self, message):
        """统一的错误响应方法"""
        return {
            'status': 'error',
            'message': message
        }
    
    def ensure_response_format(self, response_data):
        """确保响应格式正确"""
        if isinstance(response_data, dict) and 'status' in response_data:
            return response_data
        return response_data  # 如果不是字典格式，直接返回

    # 如果 error_response_dict 方法也不存在，也需要添加
    def error_response_dict(self, message):
        """错误响应（字典格式）"""
        return self.error_response(message)

    def setup_ai_client(self):
        """设置AI客户端 - 增加详细日志"""
        try:
            logger.info("开始初始化AI客户端")
            
            if not hasattr(settings, 'AI_API_KEY') or not settings.AI_API_KEY:
                logger.warning("❌ AI_API_KEY未配置，将无法使用AI功能")
                self.ai_client = None
                return
            
            try:
                import openai
                logger.info("✅ openai库导入成功")
            except ImportError as e:
                logger.error(f"❌ openai库导入失败: {e}")
                self.ai_client = None
                return
            
            api_base = getattr(settings, 'AI_API_BASE', 'https://api.siliconflow.cn/v1')
            api_key = settings.AI_API_KEY
            model_name = getattr(settings, 'AI_MODEL', 'deepseek-ai/DeepSeek-V3.1-Terminus')
            
            logger.info(f"🔧 AI配置 - API Base: {api_base}, 模型: {model_name}")
            
            self.ai_client = openai.OpenAI(
                api_key=api_key,
                base_url=api_base,
                timeout=30
            )
            
            self.model_name = model_name
            logger.info("✅ AI客户端初始化成功")
                
        except Exception as e:
            logger.error(f"❌ AI客户端初始化失败: {e}")
            logger.error(traceback.format_exc())
            self.ai_client = None

    def process_message(self, request_data):
        """处理消息路由 - 修复重复保存问题"""
        try:
            message = request_data.get('message', '').strip()
            message_type = request_data.get('message_type', 'normal_chat')
            session_id = request_data.get('session_id', 'default')
            
            logger.info(f"📨 收到消息 - 内容: {message[:100]}, 类型: {message_type}, 会话: {session_id}")
            
            # 初始化会话状态
            if session_id not in self.user_sessions:
                self.user_sessions[session_id] = {
                    'psql_used': False,
                    'query_count': 0,
                    'last_query_time': None,
                    'database_understood': False,
                    'conversation_history': [],
                    'created': datetime.now().isoformat()
                }
                logger.info(f"🆕 创建新会话: {session_id}")
            
            # 检查是否重复的连续消息
            conversation_history = self.user_sessions[session_id]['conversation_history']
            if (conversation_history and 
                conversation_history[-1].get('role') == 'user' and 
                conversation_history[-1].get('content') == message):
                logger.info("🔄 检测到重复的用户消息，跳过添加")
            else:
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
                logger.info("🎯 检测到数据分析请求")
                self.user_sessions[session_id]['psql_used'] = True
                self.user_sessions[session_id]['query_count'] += 1
                self.user_sessions[session_id]['last_query_time'] = datetime.now()
                
                # 检查是否需要数据库认知流程
                needs_database_intro = self.check_if_needs_database_intro(message, session_id)
                if needs_database_intro:
                    logger.info("🔍 需要数据库介绍流程")
                    response_data = self.handle_database_introduction(message, session_id)
                else:
                    logger.info("📊 直接进行数据分析")
                    response_data = self.handle_intelligent_data_analysis(message, session_id)
                    
                # 保存查询结果到会话缓存
                if response_data.get('status') == 'success' and response_data.get('data_count', 0) > 0:
                    self.session_data_cache[session_id] = {
                        'query_time': datetime.now(),
                        'user_message': message,
                        'data_count': response_data.get('data_count', 0),
                        'response_data': response_data
                    }
            else:
                logger.info("💬 普通聊天请求")
                response_data = self.handle_normal_chat(message, session_id)
            
            # 记录助手响应（避免重复）
            if response_data.get('status') == 'success':
                assistant_message = response_data.get('message', '')
                # 检查是否与上一条助手消息重复
                if (conversation_history and 
                    conversation_history[-1].get('role') == 'assistant' and 
                    conversation_history[-1].get('content') == assistant_message):
                    logger.info("🔄 检测到重复的助手消息，跳过添加")
                else:
                    self.user_sessions[session_id]['conversation_history'].append({
                        'role': 'assistant',
                        'content': assistant_message,
                        'timestamp': datetime.now().isoformat()
                    })
                
                # 自动保存到文件
                self.auto_save_session(session_id)
            
            logger.info(f"✅ 消息处理完成 - 状态: {response_data.get('status')}")
            return self.ensure_response_format(response_data)
            
        except Exception as e:
            logger.error(f"❌ 消息处理失败: {e}")
            logger.error(traceback.format_exc())
            return self.error_response(f"处理消息时发生错误: {str(e)}")



    def auto_save_session(self, session_id):
        """自动保存会话到文件"""
        try:
            if session_id in self.user_sessions:
                session_data = self.user_sessions[session_id]
                file_path = f"D:/code/localtxt/chat_session_{session_id}.json"
                
                save_data = {
                    'session_id': session_id,
                    'messages': session_data.get('conversation_history', []),
                    'last_updated': datetime.now().isoformat(),
                    'message_count': len(session_data.get('conversation_history', [])),
                    'metadata': {
                        'psql_used': session_data.get('psql_used', False),
                        'query_count': session_data.get('query_count', 0),
                        'last_query_time': session_data.get('last_query_time'),
                        'database_understood': session_data.get('database_understood', False),
                        'created': session_data.get('created', datetime.now().isoformat()),
                        'total_messages': len(session_data.get('conversation_history', []))
                    }
                }
                
                # 确保目录存在
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(save_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"💾 自动保存会话到文件: {file_path}, 消息数量: {save_data['message_count']}")
                
        except Exception as e:
            logger.error(f"❌ 自动保存会话失败: {e}")
            logger.error(traceback.format_exc())

    def handle_intelligent_data_analysis(self, user_message, session_id):
        """智能数据分析处理 - 增加详细日志"""
        try:
            clean_message = self.clean_psql_marker(user_message)
            logger.info(f"🔍 开始智能数据分析: {clean_message}")
            
            conversation_history = self.user_sessions[session_id].get('conversation_history', [])
            intent_analysis = self.analyze_user_intent(clean_message)
            
            logger.info(f"🎯 用户意图分析结果: {intent_analysis}")
            
            ai_available = self.ai_client is not None
            logger.info(f"🤖 AI客户端状态: {'可用' if ai_available else '不可用'}")
            
            if ai_available and self.requires_content_analysis(intent_analysis):
                logger.info("🧠 使用智能内容分析")
                return self.handle_intelligent_content_analysis(clean_message, intent_analysis, session_id, conversation_history)
            else:
                logger.info("📋 使用基础数据查询")
                return self.handle_basic_data_query(clean_message, intent_analysis, session_id)
                
        except Exception as e:
            logger.error(f"❌ 智能数据分析处理失败: {e}")
            logger.error(traceback.format_exc())
            return self.error_response_dict(f"数据分析失败: {str(e)}")

    def get_content_rich_data(self, intent_analysis):
        """获取包含content字段的详细数据 - 增加详细日志"""
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
            
            logger.info(f"📝 执行SQL查询: {base_query}")
            
            with connection.cursor() as cursor:
                cursor.execute(base_query)
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                
                logger.info(f"✅ 查询到 {len(rows)} 条记录")
                
                results = []
                for row in rows:
                    row_dict = {}
                    for i, col in enumerate(columns):
                        if col == 'notice_content' and row[i]:
                            try:
                                if isinstance(row[i], str) and row[i].strip().startswith('{'):
                                    content_data = json.loads(row[i])
                                    row_dict[col] = content_data
                                else:
                                    row_dict[col] = str(row[i])
                            except:
                                row_dict[col] = str(row[i])
                        else:
                            row_dict[col] = row[i]
                    results.append(row_dict)
                
                return results
                
        except Exception as e:
            logger.error(f"❌ 获取详细数据失败: {e}")
            logger.error(traceback.format_exc())
            return None

    def handle_intelligent_content_analysis(self, user_message, intent_analysis, session_id, conversation_history):
        """处理智能内容分析 - 增加详细日志"""
        try:
            logger.info("🧠 开始智能内容分析")
            
            raw_data = self.get_content_rich_data(intent_analysis)
        
            if not raw_data or len(raw_data) == 0:
                logger.warning("⚠️ 未找到符合条件的数据")
                return self.format_no_data_response(user_message)
        
            logger.info(f"📊 实际查询到 {len(raw_data)} 条数据")
        
            analyzed_results = self.analyze_content_data(raw_data, intent_analysis)
            logger.info(f"✅ 内容分析完成，分析 {len(analyzed_results)} 条记录")
        
            intelligent_response = self.generate_ai_enhanced_response(
                user_message, analyzed_results, intent_analysis, conversation_history
            )
        
            response_data = {
                'status': 'success',
                'response_type': 'intelligent_analysis',
                'message': intelligent_response,
                'data_count': len(raw_data),
                'analysis_depth': 'deep',
                'formatted': True,
                'actual_data_found': True
            }
        
            logger.info(f"🎉 智能分析完成，返回 {len(raw_data)} 条数据的分析结果")
            return response_data
        
        except Exception as e:
            logger.error(f"❌ 智能内容分析失败: {e}")
            logger.error(traceback.format_exc())
            return self.handle_basic_data_query(user_message, intent_analysis, session_id)

    def generate_ai_enhanced_response(self, user_message, analyzed_results, intent_analysis, conversation_history):
        """使用AI生成增强回答 - 增加详细日志"""
        logger.info("🤖 开始生成AI增强回答")
        
        data_summary = self.prepare_data_summary_for_ai(analyzed_results)
        logger.info(f"📋 准备数据摘要完成，共 {len(analyzed_results)} 条记录")
    
        prompt = f"""
作为政府采购数据分析专家，请严格按照以下数据回答用户的问题。**严禁编造或推测不存在的数据**。
用户当前问题：{user_message}
查询到的数据摘要（共{len(analyzed_results)}条记录）：
{data_summary}
**重要限制条件：**
1. 只能使用上述提供的实际数据，不能编造任何不存在的信息
2. 如果数据中没有相关内容，必须如实告知"未找到相关信息"
3. 不能推测或假设数据库中不存在的数据
4. 不能虚构地区、预算金额、时间等具体信息
5. 如果记录数量为0，必须明确说明没有找到匹配的数据
用户关注的重点：
- 行业领域：{intent_analysis['industry']}
- 查询类型：{intent_analysis['query_type']}
- 时间范围：{intent_analysis['time_range']}
请基于实际数据提供准确的回答：
"""
        try:
            logger.info("🚀 发送AI请求...")
            response = self.ai_client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.1
            )
            
            logger.info("✅ AI响应接收成功")
            ai_content = response.choices[0].message.content

            validated_content = self.validate_ai_response(ai_content, analyzed_results)
            raw_data_table = self.generate_raw_data_table(analyzed_results)
            
            logger.info("🎨 生成最终响应HTML")
            return f"""
            <div class="intelligent-analysis-result">
                <div class="analysis-content mb-4">
                    {validated_content}
                </div>
                <div class="raw-data-section mt-4">
                    <h5>📋 原始数据预览（共 {len(analyzed_results)} 条记录）</h5>
                    {raw_data_table}
                </div>
            </div>
            """
        except Exception as e:
            logger.error(f"❌ AI增强回答生成失败: {e}")
            logger.error(traceback.format_exc())
            return self.generate_template_response_with_data(user_message, analyzed_results, intent_analysis)
    
    def build_chat_context(self, conversation_history, current_message):
        """构建聊天上下文 - 简单实现"""
        try:
            logger.info(f"📚 构建聊天上下文，历史记录数: {len(conversation_history)}")
            
            messages = []
            
            # 添加系统提示
            system_prompt = """你是一个专业的政府采购数据分析助手。请根据用户的问题提供准确、有帮助的回答。"""
            messages.append({"role": "system", "content": system_prompt})
            
            # 添加历史对话（如果有的话）
            for item in conversation_history:
                role = "user" if item.get("role") == "user" else "assistant"
                content = item.get("content", "")
                if content.strip():  # 只添加非空消息
                    messages.append({"role": role, "content": content})
            
            # 添加当前消息
            messages.append({"role": "user", "content": current_message})
            
            logger.info(f"✅ 聊天上下文构建完成，共 {len(messages)} 条消息")
            return messages
            
        except Exception as e:
            logger.error(f"❌ 构建聊天上下文失败: {e}")
            # 返回最小上下文
            return [
                {"role": "system", "content": "你是专业的政府采购数据分析助手"},
                {"role": "user", "content": current_message}
            ]

    def update_conversation_history(self, session_id, user_message, assistant_response):
        """更新对话历史"""
        try:
            if session_id not in self.user_sessions:
                self.user_sessions[session_id] = {
                    'psql_used': False,
                    'query_count': 0,
                    'last_query_time': None,
                    'database_understood': False,
                    'conversation_history': []
                }
            
            # 添加用户消息
            self.user_sessions[session_id]['conversation_history'].append({
                'role': 'user',
                'content': user_message,
                'timestamp': datetime.now().isoformat()
            })
            
            # 添加助手响应
            self.user_sessions[session_id]['conversation_history'].append({
                'role': 'assistant',
                'content': assistant_response,
                'timestamp': datetime.now().isoformat()
            })
            
            # 限制历史记录长度（保留最近50条消息）
            history = self.user_sessions[session_id]['conversation_history']
            if len(history) > 50:
                self.user_sessions[session_id]['conversation_history'] = history[-50:]
                
            logger.info(f"✅ 对话历史更新完成，当前会话 {session_id} 有 {len(history)} 条记录")
            
        except Exception as e:
            logger.error(f"❌ 更新对话历史失败: {e}")

    def handle_normal_chat(self, message, session_id=None):
        """处理普通聊天 - 增加详细日志"""
        session_id = session_id or 'default'
        logger.info(f"💬 处理普通聊天消息: {message[:50]}...")
        
        session_history = self.user_sessions[session_id].get('conversation_history', [])
        messages = self.build_chat_context(session_history, message)
        
        if self.ai_client:
            try:
                logger.info("🤖 使用AI进行普通聊天")
                response = self.ai_client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    max_tokens=800,
                    temperature=0.7
                )
                
                ai_response = response.choices[0].message.content
                logger.info("✅ AI聊天响应成功")
                
                self.update_conversation_history(session_id, message, ai_response)
                
                return {
                    'status': 'success',
                    'response_type': 'normal_chat',
                    'message': ai_response,
                    'context_used': len(messages)
                }
            except Exception as e:
                logger.error(f"❌ AI聊天失败: {e}")
                logger.error(traceback.format_exc())
        
        # 备选回复
        logger.info("🔄 使用备选回复")
        return {
            'status': 'success',
            'response_type': 'normal_chat', 
            'message': '您好！我可以帮您分析政府采购数据或进行普通对话。如需数据查询，请在消息中添加 #psql 标签。'
        }

    def execute_sql_query(self, sql_query):
        """执行SQL查询 - 增加详细日志"""
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
            logger.error(f"❌ SQL执行失败: {e}")
            logger.error(traceback.format_exc())
            return None

    def handle_basic_data_query(self, user_message, intent_analysis, session_id):
        """处理基础数据查询 - 增加详细日志"""
        try:
            logger.info("📋 开始基础数据查询")
            
            target_tables = self.select_target_tables(user_message)
            sql_query = self.generate_sql_query(user_message, target_tables)
            
            if not sql_query:
                logger.error("❌ 无法生成有效的SQL查询")
                return self.error_response_dict("无法生成有效的SQL查询")
            
            logger.info(f"📝 生成的SQL: {sql_query}")
            
            query_result = self.execute_sql_query(sql_query)
            if query_result is None:
                logger.error("❌ 数据库查询失败")
                return self.error_response_dict("数据库查询失败")
            
            analysis_result = self.analyze_query_results(user_message, query_result, target_tables)
            final_response = self.format_data_analysis_response(
                user_message, sql_query, query_result, analysis_result, target_tables
            )
            
            logger.info(f"✅ 基础数据查询完成，找到 {len(query_result)} 条记录")
            return final_response
            
        except Exception as e:
            logger.error(f"❌ 基础数据查询失败: {e}")
            logger.error(traceback.format_exc())
            return self.error_response_dict(f"查询失败: {str(e)}")

    # 以下是其他必要的方法，需要根据实际情况补充
    def clean_psql_marker(self, message):
        """清理消息中的 psql 标记"""
        return re.sub(r'#psql|#p\s*s\s*q\s*l', '', message, flags=re.IGNORECASE).strip()
    
    def analyze_user_intent(self, message):
        """分析用户意图（需要实现）"""
        # 这里需要实现意图分析逻辑
        return {
            'industry': 'unknown',
            'query_type': 'general',
            'time_range': 'recent'
        }
    
    def requires_content_analysis(self, intent_analysis):
        """判断是否需要内容分析"""
        return True
    
    def build_intelligent_conditions(self, intent_analysis):
        """构建智能查询条件（需要实现）"""
        return []
    
    def analyze_content_data(self, raw_data, intent_analysis):
        """分析内容数据（需要实现）"""
        return raw_data
    
    def prepare_data_summary_for_ai(self, analyzed_results):
        """为AI准备数据摘要（需要实现）"""
        return str(analyzed_results)
    
    def validate_ai_response(self, ai_content, analyzed_results):
        """验证AI响应（需要实现）"""
        return ai_content
    
    def generate_raw_data_table(self, analyzed_results):
        """生成原始数据表格（需要实现）"""
        return "<p>数据表格预览</p>"
    
    def generate_template_response_with_data(self, user_message, analyzed_results, intent_analysis):
        """生成带数据的模板响应（需要实现）"""
        return f"<p>基于数据的响应: {user_message}</p>"
    
    def format_no_data_response(self, user_message):
        """格式化无数据响应"""
        return {
            'status': 'success',
            'message': f'未找到与"{user_message}"相关的数据。'
        }
    
    def check_if_needs_database_intro(self, message, session_id):
        """检查是否需要数据库介绍"""
        return False
    
    def handle_database_introduction(self, message, session_id):
        """处理数据库介绍流程"""
        return {
            'status': 'success',
            'message': '数据库介绍功能待实现'
        }
    
    def select_target_tables(self, user_message):
        """选择目标表（需要实现）"""
        return ['base_procurement_info_new']
    
    def generate_sql_query(self, user_message, target_tables):
        """生成SQL查询（需要实现）"""
        return "SELECT * FROM base_procurement_info_new LIMIT 10"
    
    def analyze_query_results(self, user_message, query_result, target_tables):
        """分析查询结果（需要实现）"""
        return {}
    
    def format_data_analysis_response(self, user_message, sql_query, query_result, analysis_result, target_tables):
        """格式化数据分析响应（需要实现）"""
        return {
            'status': 'success',
            'message': f'找到 {len(query_result)} 条相关记录',
            'data_count': len(query_result)
        }
