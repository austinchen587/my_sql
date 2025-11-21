import re
import logging

logger = logging.getLogger(__name__)

def convert_price_to_number(price_str):
    """
    自定义金额转换函数（与前端保持一致，修正版）
    
    Args:
       price_str: 金额字符串，如 "10万元", "1000元", "10元万元"
        
    Returns:
        float: 转换后的数字金额，转换失败返回 None
    """
    if not price_str:
        return None
    
    try:
        # 移除空格和逗号
        clean_str = str(price_str).replace(' ', '').replace(',', '')
        
        # 1. 先检查"万元"（不包含"元万元"的情况）
        if '万元' in clean_str and '元万元' not in clean_str:
            # 处理"万元"情况
            number_match = re.search(r'(\d+\.?\d*)万元', clean_str)
            if number_match:
                number_value = float(number_match.group(1))
                return number_value * 10000
        
        # 2. 处理"元万元"情况（直接提取数字，不乘以10000）
        if '元万元' in clean_str:
            number_match = re.search(r'(\d+\.?\d*)', clean_str)
            if number_match:
                number_value = float(number_match.group(1))
                return number_value
        
        # 3. 处理单独的"元"情况
        if '元' in clean_str and '万元' not in clean_str:
            number_match = re.search(r'(\d+\.?\d*)元', clean_str)
            if number_match:
                return float(number_match.group(1))
        
        # 4. 尝试直接解析为数字
        try:
            return float(clean_str)
        except ValueError:
            pass
            
    except Exception as e:
        logger.warning(f'金额转换失败: {price_str}, 错误: {e}')
    
    return None
