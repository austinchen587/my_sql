# emall_purchasing/views/utils.py
from decimal import Decimal
import json
from django.conf import settings
import logging
import traceback

logger = logging.getLogger(__name__)

def safe_json_loads(request):
    """安全解析JSON数据"""
    if hasattr(request, 'data'):
        return request.data
    try:
        return json.loads(request.body)
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析错误: {e}")
        return None

def calculate_total_quote(commodities):
    """计算商品总报价"""
    total_quote = Decimal('0')
    commodity_list = []
    
    for commodity in commodities.all():
        commodity_total = commodity.price * commodity.quantity
        total_quote += commodity_total
        commodity_list.append({
            'id': commodity.id,
            'name': commodity.name,
            'specification': commodity.specification,
            'price': float(commodity.price),
            'quantity': commodity.quantity,
            'product_url': commodity.product_url,
            'total': float(commodity_total)
        })
    
    return total_quote, commodity_list

def calculate_profit(total_budget, total_quote):
    """计算利润"""
    try:
        if isinstance(total_budget, Decimal):
            pass
        elif isinstance(total_budget, (int, float)):
            total_budget = Decimal(str(total_budget))
        elif isinstance(total_budget, str):
            total_budget = Decimal(total_budget)
        else:
            total_budget = Decimal('0')
        
        return total_budget - total_quote
    except (ValueError, TypeError):
        logger.warning(f"预算金额格式错误，使用默认值0: {total_budget}")
        return Decimal('0')

def build_client_contacts(purchasing_info):
    """构建客户联系人数组 - 从 ClientContact 模型获取"""
    try:
        contacts = []
        
        # 从 client_contacts 关联关系中获取联系人
        if hasattr(purchasing_info, 'client_contacts'):
            for contact in purchasing_info.client_contacts.all():
                contacts.append({
                    'id': contact.id,
                    'name': contact.name or '',
                    'contact_info': contact.contact_info or ''
                })
        
        # 如果没有联系人，提供默认的空联系人
        if not contacts:
            contacts.append({
                'id': 0,
                'name': '',
                'contact_info': ''
            })
        
        return contacts
        
    except Exception as e:
        logger.error(f"构建联系人信息失败: {str(e)}")
        return [{
            'id': 0,
            'name': '',
            'contact_info': ''
        }]

def build_suppliers_info(purchasing_info):
    """构建供应商信息"""
    suppliers_info = []
    
    for supplier in purchasing_info.suppliers.all():
        supplier_rel = purchasing_info.procurementsupplier_set.filter(supplier=supplier).first()
        total_quote, commodities = calculate_total_quote(supplier.commodities)
        total_budget = purchasing_info.get_total_budget()
        profit = calculate_profit(total_budget, total_quote)
        
        suppliers_info.append({
            'id': supplier.id,
            'name': supplier.name,
            'source': supplier.source,
            'contact': supplier.contact,  # 修复这里：添加了缺失的引号
            'store_name': supplier.store_name,
            'commodities': commodities,
            'total_quote': float(total_quote),
            'profit': float(profit),
            'is_selected': supplier_rel.is_selected if supplier_rel else False
        })
    
    return suppliers_info

def build_remarks_history(purchasing_info):
    """构建备注历史"""
    remarks_history = []
    all_remarks = purchasing_info.remarks_history.all().order_by('-created_at')
    
    for remark in all_remarks:
        remarks_history.append({
            'id': remark.id,
            'remark_content': remark.remark_content,
            'created_at': remark.created_at.isoformat(),
            'created_at_display': remark.created_at.strftime('%Y-%m-%d %H:%M'),
            'created_by': remark.created_by
        })
    
    return remarks_history
