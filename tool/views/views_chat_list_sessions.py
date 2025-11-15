import os, re
import json
import logging
import traceback
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)

@require_http_methods(["GET"])
def list_sessions(request):
    """列出所有会话文件 - 支持多种文件格式"""
    logger.info("📋 列出所有会话文件")
    try:
        sessions_dir = "D:/code/localtxt"
        sessions = []
        
        if os.path.exists(sessions_dir):
            for filename in os.listdir(sessions_dir):
                # 支持两种文件格式：
                # 1. chat_session_xxx.json (前端格式)
                # 2. xxx_conversation.json (后端自动保存格式)
                if (filename.startswith("chat_session_") and filename.endswith(".json")) or \
                   (filename.endswith("_conversation.json")):
                    file_path = os.path.join(sessions_dir, filename)
                    
                    session_data = None
                    try:
                        # 第一次尝试：正常读取
                        with open(file_path, 'r', encoding='utf-8') as f:
                            session_data = json.load(f)
                    except json.JSONDecodeError as e:
                        logger.warning(f"⚠️ JSON解析错误 {filename}: {e}，尝试修复...")
                        
                        # 尝试修复文件
                        session_data = try_fix_json_file(file_path, filename, e)
                        
                        if session_data is None:
                            logger.warning(f"⚠️ 无法修复文件 {filename}，跳过")
                            continue
                    
                    # 提取会话ID
                    if filename.startswith("chat_session_"):
                        session_id = filename.replace("chat_session_", "").replace(".json", "")
                    else:  # xxx_conversation.json
                        session_id = filename.replace("_conversation.json", "")
                    
                    # 计算实际消息数量
                    if 'messages' in session_data:
                        actual_message_count = len(session_data.get('messages', []))
                    elif 'conversation_history' in session_data:
                        actual_message_count = len(session_data.get('conversation_history', []))
                    else:
                        actual_message_count = 0
                    
                    # 获取最后更新时间
                    last_updated = session_data.get('last_updated')
                    if not last_updated and 'conversation_history' in session_data and session_data['conversation_history']:
                        # 使用最新消息的时间戳
                        last_message = session_data['conversation_history'][-1]
                        last_updated = last_message.get('timestamp')
                    
                    sessions.append({
                        'session_id': session_id,
                        'filename': filename,
                        'message_count': actual_message_count,
                        'last_updated': last_updated,
                        'created': session_data.get('created', session_data.get('last_updated', last_updated)),
                        'file_size': os.path.getsize(file_path)
                    })
        
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

def try_fix_json_file(file_path, filename, original_error):
    """尝试修复损坏的JSON文件"""
    try:
        logger.info(f"🔧 尝试修复文件: {filename}")
        
        # 读取原始文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 方法1: 尝试找到JSON对象的结束位置
        repaired_content = try_repair_json_content(content, filename, original_error)  # 添加original_error参数
        
        if repaired_content:
            # 验证修复后的内容
            try:
                session_data = json.loads(repaired_content)
                
                # 备份原文件
                backup_path = file_path + '.bak'
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"📦 已备份原文件到: {backup_path}")
                
                # 写入修复后的内容
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(session_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"✅ 成功修复文件: {filename}")
                return session_data
                
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ 修复后内容仍然无效: {e}")
        
        # 方法2: 如果修复失败，创建新的空会话文件
        logger.info(f"🆕 创建新的空会话文件: {filename}")
        session_id = filename.replace("chat_session_", "").replace(".json", "")
        new_session_data = {
            'session_id': session_id,
            'messages': [],
            'last_updated': datetime.now().isoformat(),
            'message_count': 0,
            'metadata': {
                'psql_used': False,
                'query_count': 0,
                'last_query_time': None,
                'database_understood': False,
                'created': datetime.now().isoformat(),
                'total_messages': 0
            }
        }
        
        # 写入新文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(new_session_data, f, ensure_ascii=False, indent=2)
        
        return new_session_data
        
    except Exception as e:
        logger.error(f"❌ 修复文件失败: {e}")
        return None

def try_repair_json_content(content, filename, original_error=None):  # 添加original_error参数并设置默认值
    """尝试修复JSON内容"""
    try:
        # 方法1: 尝试截断到最后一个完整的JSON结构
        # 查找最后一个完整的对象或数组
        brace_count = 0
        bracket_count = 0
        in_string = False
        escape_next = False
        last_valid_pos = 0
        
        for i, char in enumerate(content):
            if escape_next:
                escape_next = False
                continue
                
            if char == '\\':
                escape_next = True
                continue
                
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
                
            if not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        last_valid_pos = i + 1
                elif char == '[':
                    bracket_count += 1
                elif char == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        last_valid_pos = i + 1
        
        # 如果找到了平衡的括号，截取到那里
        if last_valid_pos > 0 and brace_count == 0 and bracket_count == 0:
            repaired = content[:last_valid_pos]
            logger.info(f"✂️ 截断到位置 {last_valid_pos}")
            return repaired
            
        # 方法2: 尝试在错误位置附近修复（只有在有错误信息时）
        if original_error:
            try:
                # 根据错误信息中的位置进行修复
                error_str = str(original_error)
                error_match = re.search(r'line (\d+) column (\d+)', error_str)
                if error_match:
                    line_num = int(error_match.group(1))
                    col_num = int(error_match.group(2))
                    
                    lines = content.split('\n')
                    if line_num <= len(lines):
                        # 简单的修复：删除错误位置后的内容
                        lines = lines[:line_num]
                        repaired = '\n'.join(lines)
                        # 确保以}或]结尾
                        if repaired.strip() and not repaired.strip().endswith(('}', ']')):
                            repaired = repaired.rstrip() + '\n}'
                        logger.info(f"🔧 基于错误位置修复")
                        return repaired
            except Exception as parse_error:
                logger.warning(f"⚠️ 解析错误信息失败: {parse_error}")
        
        # 方法3: 简单的截断修复 - 找到最后一个完整的JSON对象
        # 从末尾开始查找，找到第一个完整的{}或[]
        if content.strip().endswith(('}', ']')):
            # 如果已经以}或]结尾，尝试直接验证
            try:
                json.loads(content)
                return content
            except:
                pass
        
        # 查找最后一个完整的对象
        last_brace = content.rfind('}')
        last_bracket = content.rfind(']')
        last_valid_end = max(last_brace, last_bracket)
        
        if last_valid_end > 0:
            # 查找对应的开始位置
            if last_valid_end == last_brace:
                start_brace = content.rfind('{', 0, last_valid_end)
                if start_brace >= 0:
                    repaired = content[:last_valid_end + 1]
                    logger.info(f"🔧 截断到完整对象")
                    return repaired
            else:
                start_bracket = content.rfind('[', 0, last_valid_end)
                if start_bracket >= 0:
                    repaired = content[:last_valid_end + 1]
                    logger.info(f"🔧 截断到完整数组")
                    return repaired
        
        return None
        
    except Exception as e:
        logger.warning(f"⚠️ 修复内容时出错: {e}")
        return None
