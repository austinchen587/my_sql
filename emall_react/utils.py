# emall_react/utils.py
import re

def get_numeric_price_for_item(item):
    """
    为单个项目获取数字化价格
    """
    price_str = item.total_price_control
    if not price_str:
        return None
        
    try:
        price_str = str(price_str).strip()
        
        # 提取数字部分
        match = re.search(r'([\d,]+(?:\.\d+)?)', price_str.replace(',', ''))
        if not match:
            return None
            
        number = float(match.group(1).replace(',', ''))
        
        # 判断单位类型
        if '元万元' in price_str:
            return round(number, 2)
        elif '万元' in price_str:
            return round(number * 10000, 2)
        else:
            return None
            
    except (ValueError, TypeError, AttributeError):
        return None

def check_price_condition(numeric_price, price_condition):
    """
    检查价格是否满足条件
    """
    # 解析操作符和数值
    match = re.match(r'^\s*([><]=?|=)\s*(\d+(?:\.\d+)?)\s*$', price_condition.strip())
    
    if not match:
        return False
        
    operator = match.group(1)
    value = float(match.group(2))
    
    if operator == '>' and numeric_price > value:
        return True
    elif operator == '>=' and numeric_price >= value:
        return True
    elif operator == '<' and numeric_price < value:
        return True
    elif operator == '<=' and numeric_price <= value:
        return True
    elif operator == '=' and numeric_price == value:
        return True
        
    return False
