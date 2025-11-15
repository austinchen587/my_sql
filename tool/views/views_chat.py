# tool/views/views_chat.py
import json
import logging
import traceback
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render

# 导入 ChatMessageProcessor 类
from tool.views.views_MP.chat_processor import ChatMessageProcessor

# 配置详细的日志记录
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 创建全局处理器实例
chat_processor = ChatMessageProcessor()

@csrf_exempt
@require_http_methods(["GET", "POST"])
def chat(request):
    """统一的chat视图 - 增加详细日志"""
    logger.info(f"🌐 收到请求 - 方法: {request.method}, 路径: {request.path}")
    
    if request.method == 'GET':
        logger.info("📄 返回聊天页面")
        return render(request, 'tool/chat.html')
    
    elif request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                logger.info("📦 接收JSON数据")
            else:
                data = request.POST.dict()  # 转换为字典
                logger.info("📦 接收表单数据")
            
            if 'session_id' not in data:
                data['session_id'] = 'default'
                logger.info("🆔 使用默认会话ID")
            
            logger.info(f"🔧 请求数据: {data}")
            
            # 确保调用 process_message 并返回 JsonResponse
            response_data = chat_processor.process_message(data)
            return JsonResponse(response_data)
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON解析错误: {e}")
            return JsonResponse({
                'status': 'error', 
                'message': '数据格式错误'
            }, status=400)
        except Exception as e:
            logger.error(f"❌ 服务器内部错误: {e}")
            logger.error(traceback.format_exc())
            return JsonResponse({
                'status': 'error', 
                'message': f'服务器内部错误: {str(e)}'
            }, status=500)
