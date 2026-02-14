import re
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from dateutil import parser
from django.db import connection
from emall.models import ProcurementEmall
from bidding.models import BiddingProject, ProcurementCommodityBrand
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '将 emall 的原始数据清洗并同步到 bidding 表 (仅同步已有商品清单的项目 + 严格分类映射 + 增量更新)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--province',
            type=str,
            help='指定同步的省份代码 (JX, HN, AH, ZJ, XJ)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制全量更新所有数据',
        )

    def handle(self, *args, **options):
        target_province = options.get('province')
        force_update = options.get('force')

        # --- 1. 预加载一级分类数据 (Root Category) ---
        self.stdout.write("正在预加载一级分类映射 (procurement_emall_category)...")
        root_category_map = {}
        try:
            with connection.cursor() as cursor:
                # 假设 record_id 对应 emall 的 id
                cursor.execute("SELECT record_id, category FROM procurement_emall_category")
                rows = cursor.fetchall()
                for r_id, cat in rows:
                    root_category_map[r_id] = cat
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"加载一级分类失败或表不存在: {e}"))

        # --- 2. 预加载二级分类数据 (Sub Category) ---
        self.stdout.write("正在预加载二级分类映射 (procurement_commodity_category)...")
        sub_category_map = {}
        try:
            with connection.cursor() as cursor:
                # 假设 procurement_id 对应 emall 的 id
                cursor.execute("SELECT procurement_id, commodity_category FROM procurement_commodity_category")
                rows = cursor.fetchall()
                for p_id, c_cat in rows:
                    sub_category_map[p_id] = c_cat
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"加载二级分类失败或表不存在: {e}"))

        # --- 3. 筛选有效数据 (必须在 procurement_commodity_brand 中存在) ---
        self.stdout.write("正在筛选包含有效商品清单(Brand)的项目...")
        valid_ids = ProcurementCommodityBrand.objects.values_list('procurement_id', flat=True).distinct()
        
        # 仅查询在 valid_ids 中的项目
        raw_qs = ProcurementEmall.objects.filter(id__in=valid_ids)

        # 区域过滤
        if target_province:
            prov_map = {'JX': '江西', 'HN': '湖南', 'AH': '安徽', 'ZJ': '浙江', 'XJ': '新疆'}
            region_keyword = prov_map.get(target_province)
            if region_keyword:
                self.stdout.write(f"正在执行增量同步，目标区域：{region_keyword}...")
                raw_qs = raw_qs.filter(region__contains=region_keyword)

        total = raw_qs.count()
        self.stdout.write(f"扫描到 {total} 条有效数据，开始同步...")

        success_count = 0
        skip_count = 0
        error_count = 0
        
        # --- 4. 批量预加载已存在的 BiddingProject (用于增量比对) ---
        existing_projects = {}
        if not force_update:
            existing_projects = {
                p.source_emall_id: p 
                for p in BiddingProject.objects.only(
                    'source_emall', 'status', 'control_price', 'end_time', 
                    'title', 'root_category', 'sub_category'
                )
            }

        # --- 5. 循环处理 ---
        for raw in raw_qs:
            try:
                # --- 基础字段清洗 ---
                province = self.parse_province(raw.region)
                if not province: continue

                title = raw.project_title or raw.project_name or "无标题项目"
                mode = 'reverse' if '反拍' in title else 'bidding'
                price = self.convert_price_to_number(raw.total_price_control)
                start = self.parse_time(raw.quote_start_time)
                end = self.parse_time(raw.quote_end_time)
                new_status = self.calc_status(start, end)

                # --- 严格分类赋值 ---
                # 1. 一级分类：严格取自 procurement_emall_category，无值则默认为 'goods'
                root_cat = root_category_map.get(raw.id, 'goods')

                # 2. 二级分类：严格取自 procurement_commodity_category，无值则默认为 'service_other'
                # 注意：这里直接赋予数据库中的值，不再进行关键字推断
                sub_cat = sub_category_map.get(raw.id, 'service_other')

                # --- 增量比对逻辑 ---
                if not force_update and raw.id in existing_projects:
                    existing = existing_projects[raw.id]
                    
                    # 比对所有关键字段
                    is_same = (
                        existing.status == new_status and
                        existing.control_price == price and
                        existing.end_time == end and
                        existing.title == title and
                        existing.root_category == root_cat and
                        existing.sub_category == sub_cat
                    )
                    
                    if is_same:
                        skip_count += 1
                        continue

                # --- 执行数据库操作 ---
                BiddingProject.objects.update_or_create(
                    source_emall=raw,
                    defaults={
                        'title': title,
                        'province': province,
                        'root_category': root_cat,   # 严格映射的值
                        'sub_category': sub_cat,     # 严格映射的值
                        'mode': mode,
                        'control_price': price,
                        'start_time': start,
                        'end_time': end,
                        'status': new_status
                    }
                )
                success_count += 1
                if success_count % 50 == 0:
                    self.stdout.write(f"已更新 {success_count} 条...")

            except Exception as e:
                error_count += 1
                # 仅打印前5个错误，避免刷屏
                if error_count <= 5:
                    self.stdout.write(self.style.ERROR(f'ID {raw.id} 同步失败: {e}'))
                continue

        self.stdout.write(self.style.SUCCESS(f'同步完成！更新: {success_count}, 跳过: {skip_count}, 失败: {error_count}'))

    def parse_province(self, region_str):
        if not region_str: return None
        r = str(region_str)
        if '江西' in r: return 'JX'
        if '湖南' in r: return 'HN'
        if '安徽' in r: return 'AH'
        if '浙江' in r: return 'ZJ'
        if '新疆' in r: return 'XJ'
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