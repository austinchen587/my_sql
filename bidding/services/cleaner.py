import re
from decimal import Decimal
from django.utils import timezone
from dateutil import parser
from ..models import BiddingProject

class DataCleaner:
    """负责将 ProcurementEmall 数据转换为 BiddingProject"""

    CATEGORY_MAP = {
        '办公': 'office', '纸': 'office', '墨': 'office',
        '清洁': 'cleaning', '洗': 'cleaning',
        '电脑': 'digital', '显示器': 'digital', '相机': 'digital',
        '球': 'sports', '服': 'sports',
        '食品': 'food', '水': 'food', '油': 'food',
        # ... 更多关键词映射
    }

    @classmethod
    def sync_project(cls, emall_obj):
        # 1. 提取省份
        province_map = {'江西': 'JX', '湖南': 'HN', '安徽': 'AH', '浙江': 'ZJ'}
        province = 'JX' # 默认
        for k, v in province_map.items():
            if emall_obj.region and k in emall_obj.region:
                province = v
                break

        # 2. 提取模式 (竞价/反拍)
        mode = 'reverse' if '反拍' in (emall_obj.project_title or '') else 'bidding'

        # 3. 清洗金额
        price = None
        if emall_obj.total_price_control:
            clean_str = str(emall_obj.total_price_control).replace(',', '')
            nums = re.findall(r"[\d\.]+", clean_str)
            if nums:
                val = Decimal(nums[0])
                price = val * 10000 if '万' in emall_obj.total_price_control else val

        # 4. 清洗时间
        start = cls._parse_time(emall_obj.quote_start_time)
        end = cls._parse_time(emall_obj.quote_end_time)

        # 5. 自动归类 (简单规则，实际可接你的AI结果)
        sub_cat = 'service_other'
        title = emall_obj.project_title or ''
        for key, val in cls.CATEGORY_MAP.items():
            if key in title:
                sub_cat = val
                break
        
        # 6. 保存或更新
        BiddingProject.objects.update_or_create(
            source_emall=emall_obj,
            defaults={
                'title': title,
                'province': province,
                'root_category': 'goods', # 暂时默认为 Goods，后续对接 category 表
                'sub_category': sub_cat,
                'mode': mode,
                'control_price': price,
                'start_time': start,
                'end_time': end,
                'status': cls._calc_status(start, end)
            }
        )

    @staticmethod
    def _parse_time(time_str):
        if not time_str: return None
        try:
            dt = parser.parse(time_str.replace('.', '-'))
            return timezone.make_aware(dt) if timezone.is_naive(dt) else dt
        except: return None

    @staticmethod
    def _calc_status(start, end):
        now = timezone.now()
        if not start: return 0
        if now < start: return 0 # 即将开始
        if end and now > end: return 2 # 已结束
        return 1 # 进行中