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



@require_http_methods(["GET"])
def list_sessions(request):
    """列出所有会话文件 - 增加详细日志"""
    logger.info("📋 列出所有会话文件")
    try:
        sessions_dir = "D:/code/localtxt"
        sessions = []
        
        if os.path.exists(sessions_dir):
            for filename in os.listdir(sessions_dir):
                if filename.startswith("chat_session_") and filename.endswith(".json"):
                    file_path = os.path.join(sessions_dir, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            session_data = json.load(f)
                        
                        session_id = session_data.get('session_id', 
                                                    filename.replace("chat_session_", "").replace(".json", ""))
                        
                        sessions.append({
                            'session_id': session_id,
                            'filename': filename,
                            'message_count': session_data.get('message_count', 0),
                            'last_updated': session_data.get('last_updated'),
                            'created': session_data.get('created', session_data.get('last_updated'))
                        })
                    except Exception as e:
                        logger.warning(f"⚠️ 读取会话文件失败 {filename}: {e}")
                        continue
        
        # 按最后更新时间排序（最新的在前）
        sessions.sort(key=lambda x: x.get('last_updated', ''), reverse=True)
        
        logger.info(f"✅ 找到 {len(sessions)} 个会话文件")
        return JsonResponse({
            'status': 'success',
            'sessions': sessions,
            'total_sessions': len(sessions)
        })
        
    except Exception as e:
        logger.error(f"❌ 列出会话失败: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'获取会话列表失败: {str(e)}'
        }, status=500)
