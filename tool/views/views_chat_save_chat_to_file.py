
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
def save_chat_to_file(request):
    """保存聊天记录到文件 - 增加详细日志"""
    logger.info("💾 保存聊天记录到文件")
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        session_id = data.get('session_id', 'default')
        messages = data.get('messages', [])
        
        file_path = f"D:/code/localtxt/chat_session_{session_id}.json"
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'session_id': session_id,
                    'messages': messages,
                    'last_updated': datetime.now().isoformat(),
                    'message_count': len(messages)
                }, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 聊天记录已保存到文件: {file_path}")
            return JsonResponse({
                'status': 'success',
                'message': f'聊天记录已保存 ({len(messages)} 条消息)',
                'file_path': file_path
            })
            
        except Exception as e:
            logger.error(f"❌ 保存文件失败: {e}")
            return JsonResponse({
                'status': 'error',
                'message': f'保存失败: {str(e)}'
            }, status=500)
            
    except Exception as e:
        logger.error(f"❌ 保存聊天记录失败: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'处理请求失败: {str(e)}'
        }, status=500)
