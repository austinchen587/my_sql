# tool/views/views_MP/chat_processor_ai.py
import logging
import traceback
from django.conf import settings

logger = logging.getLogger(__name__)

class AIChatProcessor:
    """AI聊天处理器 - 专门处理普通AI聊天功能"""
    
    def __init__(self):
        self.ai_client = None
        self.model_name = None
        self.setup_ai_client()
    
    def setup_ai_client(self):
        """设置AI客户端 - 增加超时配置"""
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
                self.ai_processor.ai_client = None
                return
            
            api_base = getattr(settings, 'AI_API_BASE', 'https://api.siliconflow.cn/v1')
            api_key = settings.AI_API_KEY
            model_name = getattr(settings, 'AI_MODEL', 'deepseek-ai/DeepSeek-V3.1-Terminus')
            
            logger.info(f"🔧 AI配置 - API Base: {api_base}, 模型: {model_name}")
            
            self.ai_client = openai.OpenAI(
                api_key=api_key,
                base_url=api_base,
                timeout=60,  # 总超时时间增加到60秒
                max_retries=1  # 减少重试次数
            )
            
            self.model_name = model_name
            logger.info("✅ AI客户端初始化成功")
                
        except Exception as e:
            logger.error(f"❌ AI客户端初始化失败: {e}")
            logger.error(traceback.format_exc())
            self.ai_client = None

    def build_chat_context(self, conversation_history, current_message):
        """构建聊天上下文 - 包含完整的历史对话"""
        try:
            logger.info(f"📚 构建聊天上下文，历史记录数: {len(conversation_history)}")
            
            messages = []
            
            # 添加系统提示
            system_prompt = """请根据用户的问题和对话历史提供准确、有帮助的回答。
重要指导原则：
1. 当用户提到"上面这个数据"、"历史数据"、"刚才的数据"等时，请基于对话历史中的数据分析结果进行回答
2. 如果对话历史中包含数据查询结果，可以引用具体的数字和分析结论
3. 对于涉及已有数据的深入分析，可以提供更深入的见解
4. 如果无法找到对应的历史数据，请礼貌地请求用户提供更多信息
请确保回答基于可用的上下文信息，并且专业、准确。"""
            messages.append({"role": "system", "content": system_prompt})
            
            # 添加历史对话（完整的对话历史）
            if conversation_history:
                logger.info("📖 添加历史对话到上下文")
                for item in conversation_history:
                    role = "user" if item.get("role") == "user" else "assistant"
                    content = item.get("content", "")
                    
                    # 处理内容，确保格式正确
                    if content:
                        # 移除HTML标签（如果存在），保留纯文本内容供AI理解
                        clean_content = self.clean_html_content(content)
                        if clean_content.strip():
                            messages.append({"role": role, "content": clean_content})
                            logger.debug(f"📝 添加{role}消息: {clean_content[:100]}...")
                logger.info(f"✅ 已添加 {len(conversation_history)} 条历史消息")
            else:
                logger.info("📭 无历史对话记录")
            
            # 添加当前消息
            messages.append({"role": "user", "content": current_message})
            
            logger.info(f"✅ 聊天上下文构建完成，共 {len(messages)} 条消息")
            return messages
            
        except Exception as e:
            logger.error(f"❌ 构建聊天上下文失败: {e}")
            logger.error(traceback.format_exc())
            # 返回最小上下文
            return [
                {"role": "system", "content": "你是专业的政府采购数据分析助手"},
                {"role": "user", "content": current_message}
            ]
        


    def clean_html_content(self, html_content):
        """清理HTML内容，提取纯文本供AI理解"""
        try:
            if not html_content or not isinstance(html_content, str):
                return str(html_content) if html_content else ""
            
            # 如果是纯文本，直接返回
            if '<' not in html_content and '>' not in html_content:
                return html_content
            
            # 简单的HTML标签清理
            import re
            # 移除HTML标签但保留内容
            clean_text = re.sub(r'<[^>]+>', ' ', html_content)
            # 合并多个空格
            clean_text = re.sub(r'\s+', ' ', clean_text)
            # 移除多余的换行
            clean_text = re.sub(r'\n+', '\n', clean_text)
            
            # 特别处理AI分析结果中的关键信息
            if '智能分析结果' in html_content or '数据预览' in html_content:
                # 提取表格数据摘要
                table_match = re.search(r'共\s*(\d+)\s*条记录', html_content)
                if table_match:
                    record_count = table_match.group(1)
                    clean_text += f" （包含{record_count}条数据记录）"
            
            return clean_text.strip()
            
        except Exception as e:
            logger.warning(f"⚠️ HTML内容清理失败，使用原始内容: {e}")
            return html_content

    def handle_normal_chat(self, message, session_history=None):
        """处理普通聊天 - 增加详细日志"""
        session_history = session_history or []
        logger.info(f"💬 处理普通聊天消息: {message[:50]}...")
        
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
                
                return ai_response
                
            except Exception as e:
                logger.error(f"❌ AI聊天失败: {e}")
                logger.error(traceback.format_exc())
        
        # 备选回复
        logger.info("🔄 使用备选回复")
        return '您好！我可以帮您分析政府采购数据或进行普通对话。如需数据查询，请在消息中添加 #psql 标签。'
