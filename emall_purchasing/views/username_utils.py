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
