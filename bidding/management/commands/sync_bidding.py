import re
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from dateutil import parser
from django.db import connection
from emall.models import ProcurementEmall
from bidding.models import BiddingProject
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '将 emall 的原始数据清洗并同步到 bidding 表 (已接入 category 分类表 + 智能关键词兜底)'

    def handle(self, *args, **options):
        # 1. 预加载分类数据
        self.stdout.write("正在预加载分类数据 (procurement_emall_category)...")
        category_map = {}
        try:
            with connection.cursor() as cursor:
                # 注意：这里假设分类表的 record_id 对应 ProcurementEmall 的 id
                cursor.execute("SELECT record_id, category FROM procurement_emall_category")
                rows = cursor.fetchall()
                for r_id, cat in rows:
                    category_map[r_id] = cat
            self.stdout.write(f"分类数据加载完成，共 {len(category_map)} 条")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"分类表读取失败 (可能是表名不对?): {e}，后续将完全依赖关键词分类"))

        # 2. 开始同步主逻辑
        raw_qs = ProcurementEmall.objects.all()
        total = raw_qs.count()
        self.stdout.write(f"正在同步 {total} 条原始数据...")

        success_count = 0
        error_count = 0
        
        for raw in raw_qs:
            try:
                # --- 提取标题 ---
                title = raw.project_title or raw.project_name or "无标题项目"
                
                # --- 提取省份 ---
                province = self.parse_province(raw.region)
                if not province: continue

                # --- 提取模式 ---
                mode = 'reverse' if '反拍' in title else 'bidding'

                # --- 价格清洗 ---
                price = self.convert_price_to_number(raw.total_price_control)

                # --- 清洗时间 ---
                start = self.parse_time(raw.quote_start_time)
                end = self.parse_time(raw.quote_end_time)

                # =========================================================
                # [核心修复] 确定 root_category (大类)
                # 逻辑：先查表 -> 表里没有就查标题关键词 -> 都没有才默认为 goods
                # =========================================================
                db_cat = category_map.get(raw.id)
                
                if db_cat in ['goods', 'project', 'service']:
                    root_cat = db_cat
                else:
                    # 兜底逻辑：根据标题关键词进行补救
                    if any(k in title for k in ['工程', '施工', '改造', '修缮', '建设', '安装', '装修', '整治']):
                        root_cat = 'project'
                    elif any(k in title for k in ['服务', '维保', '检测', '租赁', '运维', '保养', '外包', '物业']):
                        root_cat = 'service'
                    else:
                        root_cat = 'goods' # 实在无法识别，归为物资

                # --- 确定 sub_category (子类) ---
                # 基于标题的简单规则，用于细分标签
                sub_cat = 'service_other'
                title_search = title 
                if any(k in title_search for k in ['办公', '纸', '墨']): sub_cat = 'office'
                elif any(k in title_search for k in ['清洁', '洗', '扫']): sub_cat = 'cleaning'
                elif any(k in title_search for k in ['电脑', '数码', '屏', '显']): sub_cat = 'digital'
                elif any(k in title_search for k in ['球', '服', '体育']): sub_cat = 'sports'
                elif any(k in title_search for k in ['工', '机', '泵', '阀', '梯', '设施']): sub_cat = 'industrial'
                elif any(k in title_search for k in ['食', '水', '油', '米']): sub_cat = 'food'

                # --- 保存到 BiddingProject 表 ---
                BiddingProject.objects.update_or_create(
                    source_emall=raw,
                    defaults={
                        'title': title,
                        'province': province,
                        'root_category': root_cat,  # <--- 使用修复后的分类
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
                error_count += 1
                # 只打印前5个错误，避免刷屏
                if error_count <= 5:
                    self.stdout.write(self.style.ERROR(f'ID {raw.id} 同步失败: {e}'))
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
                match = re.search(r'(\d+\.?\d*)万元', clean_str)
                if match: return float(match.group(1)) * 10000
            if '元万元' in clean_str:
                match = re.search(r'(\d+\.?\d*)', clean_str)
                if match: return float(match.group(1))
            if '元' in clean_str and '万元' not in clean_str:
                match = re.search(r'(\d+\.?\d*)元', clean_str)
                if match: return float(match.group(1))
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