import re
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from dateutil import parser
from emall.models import ProcurementEmall
from bidding.models import BiddingProject
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '将 emall 的原始数据清洗并同步到 bidding 表 (调试模式)'

    def handle(self, *args, **options):
        raw_qs = ProcurementEmall.objects.all()
        total = raw_qs.count()
        self.stdout.write(f"正在同步 {total} 条原始数据...")

        success_count = 0
        error_count = 0
        
        for raw in raw_qs:
            try:
                # 1. 提取标题
                title = raw.project_title or raw.project_name or "无标题项目"
                
                # 2. 提取省份
                province = self.parse_province(raw.region)
                # [修改] 兜底策略：如果识别不出省份，默认归为江西，防止数据丢失
                if not province:
                    continue  # <--- 改回 continue，不要用 'JX' 兜底了

                # 3. 提取模式
                mode = 'reverse' if '反拍' in title else 'bidding'

                # 4. 价格清洗
                price = self.convert_price_to_number(raw.total_price_control)

                # 5. 清洗时间
                start = self.parse_time(raw.quote_start_time)
                end = self.parse_time(raw.quote_end_time)

                # 6. 分类规则
                sub_cat = 'service_other'
                title_search = title 
                if any(k in title_search for k in ['办公', '纸', '墨']): sub_cat = 'office'
                elif any(k in title_search for k in ['清洁', '洗', '扫']): sub_cat = 'cleaning'
                elif any(k in title_search for k in ['电脑', '数码', '屏']): sub_cat = 'digital'
                elif any(k in title_search for k in ['球', '服', '体育']): sub_cat = 'sports'
                elif any(k in title_search for k in ['工', '机', '泵']): sub_cat = 'industrial'
                elif any(k in title_search for k in ['食', '水', '油', '米']): sub_cat = 'food'

                # 7. 保存 (自动关联主键)
                BiddingProject.objects.update_or_create(
                    source_emall=raw,
                    defaults={
                        'title': title,
                        'province': province,
                        'root_category': 'goods',
                        'sub_category': sub_cat,
                        'mode': mode,
                        'control_price': price,
                        'start_time': start,
                        'end_time': end,
                        'status': self.calc_status(start, end)
                    }
                )
                success_count += 1
                if success_count % 100 == 0:
                    self.stdout.write(f"已处理 {success_count}...")

            except Exception as e:
                # [修改] 打印具体的错误信息，方便排查
                error_count += 1
                self.stdout.write(self.style.ERROR(f'ID {raw.id} 同步失败: {e}'))
                # 如果错误太多，只打印前5个，避免刷屏
                if error_count > 5:
                    self.stdout.write(self.style.ERROR('错误过多，建议先检查数据库结构...'))
                    break
                continue

        self.stdout.write(self.style.SUCCESS(f'同步完成！成功: {success_count}, 失败: {error_count}'))

    def parse_province(self, region_str):
        if not region_str: return None
        r = str(region_str)
        if '江西' in r: return 'JX'
        if '湖南' in r: return 'HN'
        if '安徽' in r: return 'AH'
        if '浙江' in r: return 'ZJ'
        return None

    def convert_price_to_number(self, price_str):
        if not price_str: return None
        try:
            clean_str = str(price_str).replace(' ', '').replace(',', '')
            if '万元' in clean_str and '元万元' not in clean_str:
                number_match = re.search(r'(\d+\.?\d*)万元', clean_str)
                if number_match: return float(number_match.group(1)) * 10000
            if '元万元' in clean_str:
                number_match = re.search(r'(\d+\.?\d*)', clean_str)
                if number_match: return float(number_match.group(1))
            if '元' in clean_str and '万元' not in clean_str:
                number_match = re.search(r'(\d+\.?\d*)元', clean_str)
                if number_match: return float(number_match.group(1))
            try: return float(clean_str)
            except ValueError: pass
        except: return None
        return None

    def parse_time(self, time_str):
        if not time_str: return None
        try:
            dt = parser.parse(str(time_str).replace('.', '-'))
            return timezone.make_aware(dt) if timezone.is_naive(dt) else dt
        except: return None

    def calc_status(self, start, end):
        now = timezone.now()
        if not start: return 0
        if now < start: return 0
        if end and now > end: return 2
        return 1