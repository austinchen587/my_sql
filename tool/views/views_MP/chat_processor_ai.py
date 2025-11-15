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
