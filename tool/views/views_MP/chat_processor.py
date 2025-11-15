# tool/views/views_MP/chat_processor.py
import os
import json
import logging
import traceback
from datetime import datetime
from django.conf import settings
from decimal import Decimal

# 导入功能模块
from .chat_processor_ai import AIChatProcessor
from .chat_processor_psql import PSQLDataProcessor


# 配置详细的日志记录
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ChatMessageProcessor:
    """聊天消息处理器 - 主控制器"""
    
    def __init__(self):
        self.ai_chat_processor = AIChatProcessor()  # AI聊天处理器
        self.psql_processor = PSQLDataProcessor(self.ai_chat_processor)  # PSQL数据处理器
        self.user_sessions = {}
        self.session_data_cache = {}
        
        # 添加保存目录
        self.save_dir = "D:/code/localtxt"  # 或者其他你想要的路径
        os.makedirs(self.save_dir, exist_ok=True)  # 确保目录存在
        
        logger.info(f"📁 确保保存目录存在: {self.save_dir}")
        logger.info("ChatMessageProcessor 初始化完成")

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
        return response_data

    def process_message(self, request_data):
        """处理消息路由 - 主入口"""
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
                needs_database_intro = self.psql_processor.check_if_needs_database_intro(message, session_id)
                if needs_database_intro:
                    logger.info("🔍 需要数据库介绍流程")
                    response_data = self.psql_processor.handle_database_introduction(message, session_id)
                else:
                    logger.info("📊 直接进行数据分析")
                    response_data = self.psql_processor.handle_intelligent_data_analysis(message, session_id, self.user_sessions)
                    
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
        

    def handle_normal_chat(self, message, session_id=None):
        """处理普通聊天 - 包含完整会话历史"""
        session_id = session_id or 'default'
        logger.info(f"💬 处理普通聊天消息: {message[:50]}...")
        
        # 获取当前会话的完整历史记录
        session_data = self.user_sessions.get(session_id, {})
        session_history = session_data.get('conversation_history', [])
        
        logger.info(f"📋 当前会话历史记录数: {len(session_history)}")
        
        # 检查是否涉及历史数据的引用
        if self.contains_data_reference(message):
            logger.info("🔍 检测到对历史数据的引用")
            # 尝试从缓存中获取最近的数据结果
            recent_data = self.get_recent_data_for_context(session_id)
            if recent_data:
                message = self.enrich_message_with_data_context(message, recent_data)
                logger.info("✅ 已为消息添加上下文数据")
        
        # 使用AI处理器处理普通聊天，传入完整历史
        ai_response = self.ai_chat_processor.handle_normal_chat(message, session_history)
        
        return {
            'status': 'success',
            'response_type': 'normal_chat',
            'message': ai_response,
            'context_used': len(session_history)
        }
    def contains_data_reference(self, message):
        """检查消息是否包含对历史数据的引用"""
        reference_keywords = [
            '上面', '刚才', '之前', '历史数据', '这个数据', '这些数据',
            '上面这个', '刚才的', '前述', '上文', '刚才那个'
        ]
        
        message_lower = message.lower()
        for keyword in reference_keywords:
            if keyword in message_lower:
                return True
        return False
    def get_recent_data_for_context(self, session_id):
        """获取最近的查询数据作为上下文"""
        try:
            if session_id in self.session_data_cache:
                cache_data = self.session_data_cache[session_id]
                # 检查数据是否还在有效期内（30分钟内）
                from datetime import datetime, timedelta
                if cache_data.get('query_time') and \
                datetime.now() - cache_data['query_time'] < timedelta(minutes=30):
                    return cache_data
            return None
        except Exception as e:
            logger.warning(f"⚠️ 获取数据缓存失败: {e}")
            return None
    def enrich_message_with_data_context(self, message, recent_data):
        """为消息添加数据上下文"""
        try:
            data_context = f"""
    用户正在引用之前的数据分析结果。最近的查询信息：
    - 查询时间：{recent_data.get('query_time', '未知')}
    - 数据量：{recent_data.get('data_count', 0)} 条记录
    - 原始问题：{recent_data.get('user_message', '未知')}
    当前用户消息：{message}
    请基于上述上下文进行回答。
            """.strip()
            
            return data_context
        except Exception as e:
            logger.warning(f"⚠️ 添加上下文失败: {e}")
            return message
        






    
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


    def auto_save_session(self, session_id):
        """自动保存会话到文件 - 修复覆盖问题"""
        try:
            session_data = self.user_sessions.get(session_id)
            if not session_data:
                return
            
            # 确保保存目录存在
            if not hasattr(self, 'save_dir'):
                self.save_dir = "D:/code/localtxt"
                os.makedirs(self.save_dir, exist_ok=True)
            
            # 先尝试读取现有文件内容（如果存在）
            filename = f"{session_id}_conversation.json"
            filepath = os.path.join(self.save_dir, filename)
            
            existing_data = {}
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                    logger.info(f"📖 读取现有会话文件: {filepath}")
                except Exception as e:
                    logger.warning(f"⚠️ 读取现有文件失败，创建新文件: {e}")
            
            # 合并数据，而不是覆盖
            merged_data = self.merge_session_data(existing_data, session_data)
            
            # 深度处理会话数据，确保所有字段可序列化
            def make_json_serializable(data):
                """递归处理数据使其可JSON序列化"""
                from datetime import datetime, date
                from decimal import Decimal
                
                if isinstance(data, dict):
                    return {k: make_json_serializable(v) for k, v in data.items()}
                elif isinstance(data, list):
                    return [make_json_serializable(item) for item in data]
                elif isinstance(data, datetime):
                    return data.isoformat()
                elif isinstance(data, date):
                    return data.isoformat()
                elif isinstance(data, Decimal):
                    return float(data)
                elif hasattr(data, '__dict__'):
                    return make_json_serializable(data.__dict__)
                else:
                    return data
            
            # 转换会话数据
            serializable_data = make_json_serializable(merged_data)
            
            # 保存到文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(serializable_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 会话已保存: {filepath}")
            
        except Exception as e:
            logger.error(f"❌ 自动保存会话失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
    def merge_session_data(self, existing_data, new_data):
        """合并会话数据，保留历史记录"""
        merged = existing_data.copy() if existing_data else {}
        
        # 合并基础字段
        merged.update({
            'psql_used': new_data.get('psql_used', False),
            'query_count': new_data.get('query_count', 0),
            'last_query_time': new_data.get('last_query_time'),
            'database_understood': new_data.get('database_understood', False),
            'last_updated': new_data.get('last_updated') or new_data.get('created')
        })
        
        # 合并对话历史（去重合并）
        existing_history = existing_data.get('conversation_history', [])
        new_history = new_data.get('conversation_history', [])
        
        # 使用去重方法合并历史记录
        merged_history = self.merge_conversation_history(existing_history, new_history)
        
        # 限制历史记录长度（保留最近100条消息）
        max_history = 100
        if len(merged_history) > max_history:
            merged_history = merged_history[-max_history:]
        
        merged['conversation_history'] = merged_history
        
        # 确保有创建时间
        if 'created' not in merged:
            merged['created'] = new_data.get('created')
        
        return merged
    def merge_conversation_history(self, existing_history, new_history):
        """合并对话历史，避免重复"""
        if not existing_history:
            return new_history
        
        if not new_history:
            return existing_history
        
        # 使用时间戳作为唯一标识
        existing_timestamps = {msg.get('timestamp') for msg in existing_history if msg.get('timestamp')}
        
        # 添加新消息（只添加时间戳不存在的消息）
        merged_history = existing_history.copy()
        
        for new_msg in new_history:
            if new_msg.get('timestamp') not in existing_timestamps:
                merged_history.append(new_msg)
        
        # 按时间排序
        merged_history.sort(key=lambda x: x.get('timestamp', ''))
        
        return merged_history
    

    def contains_data_reference(self, message):
        """检查消息是否包含对历史数据的引用"""
        reference_keywords = [
            '上面', '刚才', '之前', '历史数据', '这个数据', '这些数据',
            '上面这个', '刚才的', '前述', '上文', '刚才那个', '分析数据',
            '分析刚才', '分析之前', '分析上文', '分析这些'
        ]
        
        message_lower = message.lower()
        for keyword in reference_keywords:
            if keyword in message_lower:
                return True
        
        # 检查是否包含"分析"+"数据"的组合
        if '分析' in message_lower and any(word in message_lower for word in ['数据', '这个', '刚才', '上面']):
            return True
        
        return False
    def enrich_message_with_data_context(self, message, recent_data):
        """为消息添加数据上下文"""
        try:
            data_context = f"""
    用户正在引用之前的数据分析结果。最近的查询信息：
    - 查询时间：{recent_data.get('query_time', '未知')}
    - 数据量：{recent_data.get('data_count', 0)} 条记录
    - 原始问题：{recent_data.get('user_message', '未知')}
    当前用户消息：{message}
    请基于上述上下文进行回答，特别是要参考之前的数据分析结果。
            """.strip()
            
            return data_context
        except Exception as e:
            logger.warning(f"⚠️ 添加上下文失败: {e}")
            return message




    def _simple_remove_duplicates(self, messages):
        """简单的去重方法（备用）"""
        if not messages:
            return []
        
        seen = set()
        unique_messages = []
        
        for msg in messages:
            content = msg.get('content', '')
            role = msg.get('role', '')
            key = f"{role}:{content}"
            
            if key not in seen:
                seen.add(key)
                unique_messages.append(msg)
        
        return unique_messages

    

    







    def sanitize_json_content(self, content):
        """清理JSON内容中的特殊字符"""
        if not content:
            return content
        
        # 移除或转义可能破坏JSON的字符
        content = content.replace('\\', '\\\\')  # 转义反斜杠
        content = content.replace('"', '\\"')    # 转义双引号
        content = content.replace('\n', '\\n')   # 转义换行符
        content = content.replace('\t', '\\t')   # 转义制表符
        content = content.replace('\r', '\\r')   # 转义回车符
        
        return content
    

    def remove_duplicate_messages(self, messages):
        """移除重复的消息，保留最新的一个"""
        if not messages:
            return []
        
        seen_content = set()
        unique_messages = []
        
        # 从最新到最旧遍历，保留第一次出现的内容
        for message in reversed(messages):
            content = message.get('content', '')
            role = message.get('role', '')
            
            # 只对用户消息进行去重
            if role == 'user' and content:
                if content not in seen_content:
                    seen_content.add(content)
                    unique_messages.append(message)
            else:
                # 助手消息直接保留
                unique_messages.append(message)
        
        # 恢复原始顺序
        return list(reversed(unique_messages))
