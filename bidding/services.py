import re
from decimal import Decimal
from django.utils import timezone
from dateutil import parser
from bidding.models import BiddingProject
import logging

logger = logging.getLogger(__name__)

def sync_single_project(raw_obj):
    """
    核心清洗函数：将单个 emall 对象同步到 bidding 表
    """
    try:
        # 1. 提取标题
        title = raw_obj.project_title or raw_obj.project_name or "无标题项目"
        
        # 2. 提取省份 (严格匹配)
        region_str = str(raw_obj.region)
        province = None
        if '江西' in region_str: province = 'JX'
        elif '湖南' in region_str: province = 'HN'
        elif '安徽' in region_str: province = 'AH'
        elif '浙江' in region_str: province = 'ZJ'
        
        # 如果不是这4个省，直接忽略，不入库
        if not province:
            return None

        # 3. 提取模式
        mode = 'reverse' if '反拍' in title else 'bidding'

        # 4. 清洗价格 (复用之前的严格逻辑)
        price = parse_price(raw_obj.total_price_control)

        # 5. 清洗时间
        start = parse_time(raw_obj.quote_start_time)
        end = parse_time(raw_obj.quote_end_time)

        # 6. 简单的分类规则
        sub_cat = 'service_other'
        title_search = title 
        if any(k in title_search for k in ['办公', '纸', '墨']): sub_cat = 'office'
        elif any(k in title_search for k in ['清洁', '洗', '扫']): sub_cat = 'cleaning'
        elif any(k in title_search for k in ['电脑', '数码', '屏']): sub_cat = 'digital'
        elif any(k in title_search for k in ['球', '服', '体育']): sub_cat = 'sports'
        elif any(k in title_search for k in ['工', '机', '泵']): sub_cat = 'industrial'
        elif any(k in title_search for k in ['食', '水', '油', '米']): sub_cat = 'food'

        # 7. 保存到数据库
        obj, created = BiddingProject.objects.update_or_create(
            source_emall=raw_obj,
            defaults={
                'title': title,
                'province': province,
                'root_category': 'goods',
                'sub_category': sub_cat,
                'mode': mode,
                'control_price': price,
                'start_time': start,
                'end_time': end,
                'status': calc_status(start, end)
            }
        )
        return obj

    except Exception as e:
        logger.error(f"同步失败 ID {raw_obj.id}: {str(e)}")
        return None

# --- 辅助工具函数 ---
def parse_price(price_str):
    if not price_str: return None
    try:
        clean_str = str(price_str).replace(' ', '').replace(',', '')
        if '万元' in clean_str and '元万元' not in clean_str:
            match = re.search(r'(\d+\.?\d*)万元', clean_str)
            if match: return float(match.group(1)) * 10000
        if '元' in clean_str or '元万元' in clean_str:
            match = re.search(r'(\d+\.?\d*)', clean_str)
            if match: return float(match.group(1))
        return float(clean_str)
    except: return None

def parse_time(time_str):
    if not time_str: return None
    try:
        dt = parser.parse(str(time_str).replace('.', '-'))
        return timezone.make_aware(dt) if timezone.is_naive(dt) else dt
    except: return None

def calc_status(start, end):
    now = timezone.now()
    if not start: return 0
    if now < start: return 0
    if end and now > end: return 2
    return 1