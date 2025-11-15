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
    """从文件加载聊天记录 - 支持多种文件格式"""
    logger.info("📂 从文件加载聊天记录")
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        session_id = data.get('session_id', 'default')
        
        # 尝试两种文件格式
        file_paths = [
            f"D:/code/localtxt/chat_session_{session_id}.json",  # 前端格式
            f"D:/code/localtxt/{session_id}_conversation.json"    # 后端格式
        ]
        
        session_data = None
        loaded_file_path = None
        
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                    loaded_file_path = file_path
                    logger.info(f"✅ 从文件加载聊天记录成功: {file_path}")
                    break
            except Exception as e:
                logger.warning(f"⚠️ 无法加载文件 {file_path}: {e}")
                continue
        
        if session_data:
            # 兼容不同的数据格式
            if 'messages' in session_data:
                messages = session_data['messages']
            elif 'conversation_history' in session_data:
                messages = session_data['conversation_history']
            else:
                messages = []
            
            return JsonResponse({
                'status': 'success',
                'session_id': session_id,
                'messages': messages,
                'last_updated': session_data.get('last_updated'),
                'message_count': len(messages),
                'file_path': loaded_file_path
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
        logger.error(f"❌ 加载聊天记录失败: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'加载失败: {str(e)}'
        }, status=500)