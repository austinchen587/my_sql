import re
from decimal import Decimal
from django.utils import timezone
from dateutil import parser
from django.db import connection # [新增]
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
        
        # 2. 提取省份
        region_str = str(raw_obj.region)
        province = None
        if '江西' in region_str: province = 'JX'
        elif '湖南' in region_str: province = 'HN'
        elif '安徽' in region_str: province = 'AH'
        elif '浙江' in region_str: province = 'ZJ'
        
        if not province: return None

        # 3. 提取模式
        mode = 'reverse' if '反拍' in title else 'bidding'

        # 4. 清洗价格
        price = parse_price(raw_obj.total_price_control)

        # 5. 清洗时间
        start = parse_time(raw_obj.quote_start_time)
        end = parse_time(raw_obj.quote_end_time)

        # 6. [核心修改] 查库获取 root_category
        root_cat = 'goods' # 默认值
        try:
            with connection.cursor() as cursor:
                # 根据 record_id (即 raw_obj.id) 查找分类
                cursor.execute(
                    "SELECT category FROM procurement_emall_category WHERE record_id = %s LIMIT 1", 
                    [raw_obj.id]
                )
                row = cursor.fetchone()
                if row:
                    db_cat = row[0]
                    if db_cat in ['goods', 'project', 'service']:
                        root_cat = db_cat
        except Exception as db_e:
            logger.warning(f"单个同步时查询分类失败: {db_e}")

        # 7. 简单的子分类规则 (Sub Category)
        sub_cat = 'service_other'
        title_search = title 
        if any(k in title_search for k in ['办公', '纸', '墨']): sub_cat = 'office'
        elif any(k in title_search for k in ['清洁', '洗', '扫']): sub_cat = 'cleaning'
        elif any(k in title_search for k in ['电脑', '数码', '屏']): sub_cat = 'digital'
        elif any(k in title_search for k in ['球', '服', '体育']): sub_cat = 'sports'
        elif any(k in title_search for k in ['工', '机', '泵']): sub_cat = 'industrial'
        elif any(k in title_search for k in ['食', '水', '油', '米']): sub_cat = 'food'

        # 8. 保存到数据库
        obj, created = BiddingProject.objects.update_or_create(
            source_emall=raw_obj,
            defaults={
                'title': title,
                'province': province,
                'root_category': root_cat, # <--- 使用查到的分类
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

# --- 辅助工具函数保持不变 ---
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