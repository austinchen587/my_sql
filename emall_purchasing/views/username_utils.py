# emall_purchasing/views/username_utils.py
import logging
import base64
import urllib.parse

logger = logging.getLogger(__name__)

def decode_username_from_header(encoded_username):
    """解码前端传递的用户名"""
    if not encoded_username:
        return encoded_username
        
    try:
        # 先尝试 Base64 解码
        try:
            decoded_bytes = base64.b64decode(encoded_username)
            decoded_str = decoded_bytes.decode('utf-8')
            logger.info(f"Base64 解码成功: {decoded_str}")
            return decoded_str
        except:
            # 如果 Base64 解码失败，尝试 URL 解码
            decoded_str = urllib.parse.unquote(encoded_username)
            logger.info(f"URL 解码成功: {decoded_str}")
            return decoded_str
    except Exception as e:
        logger.warning(f"用户名解码失败，使用原始值: {encoded_username}, 错误: {str(e)}")
        return encoded_username

def get_username_from_request(request):
    """从请求中获取用户名（多种方式尝试）"""
    username = "未知用户"
    
    # 1. 首先尝试从cookies获取username并解码
    username_from_cookie = request.COOKIES.get('username')
    if username_from_cookie:
        username = urllib.parse.unquote(username_from_cookie)
        logger.info(f"从cookie获取并解码用户名: {username}")
    
    # 2. 如果cookie中没有，尝试从session获取
    elif request.session.get('username'):
        username = request.session['username']
        logger.info(f"从session获取用户名: {username}")
    
    # 3. 如果session中没有，尝试从认证用户获取
    elif hasattr(request, 'user') and request.user.is_authenticated:
        username = request.user.username
        logger.info(f"从认证用户获取用户名: {username}")
    
    # 4. 如果都没有，尝试从请求头获取并解码
    elif request.META.get('HTTP_X_USERNAME'):
        encoded_username = request.METAget('HTTP_X_USERNAME')
        username = decode_username_from_header(encoded_username)
        logger.info(f"从请求头获取并解码用户名: {username}")
    
    else:
        logger.warning("无法获取用户信息，使用'未知用户'")
    
    return username