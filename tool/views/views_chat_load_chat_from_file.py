import os
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


# 配置详细的日志记录
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def load_chat_from_file(request):
    """从文件加载聊天记录 - 增加详细日志"""
    logger.info("📂 从文件加载聊天记录")
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        session_id = data.get('session_id', 'default')
        
        # 从文件加载的逻辑
        file_path = f"D:/code/localtxt/chat_session_{session_id}.json"
        
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                # 兼容新旧数据格式
                if 'messages' in session_data:
                    messages = session_data['messages']
                else:
                    # 旧格式兼容
                    messages = session_data.get('conversation_history', [])
                
                logger.info(f"✅ 从文件加载聊天记录成功: {file_path}")
                return JsonResponse({
                    'status': 'success',
                    'session_id': session_id,
                    'messages': messages,
                    'last_updated': session_data.get('last_updated'),
                    'message_count': len(messages),
                    'metadata': session_data.get('metadata', {})
                })
            else:
                logger.info("📝 会话文件不存在，创建新的空会话")
                return JsonResponse({
                    'status': 'success',
                    'session_id': session_id,
                    'messages': [],
                    'message_count': 0,
                    'message': '会话文件不存在，创建新的空会话'
                })
                
        except Exception as e:
            logger.error(f"❌ 加载文件失败: {e}")
            return JsonResponse({
                'status': 'error',
                'message': f'加载失败: {str(e)}'
            }, status=500)
            
    except Exception as e:
        logger.error(f"❌ 加载聊天记录失败: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'处理请求失败: {str(e)}'
        }, status=500)