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
    help = '将 emall 数据同步到 bidding 表 (严格映射分类表 + 仅同步有Brand清单的项目 + 增量更新)'

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

        # =================================================================
        # 1. 预加载分类映射表 (避免 N+1 查询)
        # =================================================================
        
        # 1.1 加载一级分类 (Root Category)
        # 来源表: procurement_emall_category
        # 逻辑: record_id (emall_id) -> category (goods, project, service)
        self.stdout.write("正在预加载一级分类映射 (procurement_emall_category)...")
        root_category_map = {}
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT record_id, category FROM procurement_emall_category")
                rows = cursor.fetchall()
                for r_id, cat in rows:
                    root_category_map[r_id] = cat
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"加载一级分类失败: {e}"))

        # 1.2 加载二级分类 (Sub Category)
        # 来源表: procurement_commodity_category
        # 逻辑: procurement_id (emall_id) -> commodity_category (中文名称)
        self.stdout.write("正在预加载二级分类映射 (procurement_commodity_category)...")
        sub_category_raw_map = {}
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT procurement_id, commodity_category FROM procurement_commodity_category")
                rows = cursor.fetchall()
                for p_id, c_cat in rows:
                    sub_category_raw_map[p_id] = c_cat
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"加载二级分类失败: {e}"))

        # =================================================================
        # 2. 确定同步范围 (过滤逻辑)
        # =================================================================
        
        self.stdout.write("正在筛选包含有效商品清单(Brand)的项目...")
        # 核心过滤条件：必须在 procurement_commodity_brand 表中有记录
        valid_ids = ProcurementCommodityBrand.objects.values_list('procurement_id', flat=True).distinct()
        
        # 基础查询集
        raw_qs = ProcurementEmall.objects.filter(id__in=valid_ids)

        # 区域增量过滤
        if target_province:
            prov_map = {'JX': '江西', 'HN': '湖南', 'AH': '安徽', 'ZJ': '浙江', 'XJ': '新疆'}
            region_keyword = prov_map.get(target_province)
            if region_keyword:
                self.stdout.write(f"正在执行区域筛选，目标区域：{region_keyword}...")
                raw_qs = raw_qs.filter(region__contains=region_keyword)

        total = raw_qs.count()
        self.stdout.write(f"扫描到 {total} 条有效数据，开始同步...")

        # =================================================================
        # 3. 预加载存量数据 (用于增量比对)
        # =================================================================
        existing_projects = {}
        if not force_update:
            # 必须加载所有参与比对的字段，包括 title 和 category
            existing_projects = {
                p.source_emall_id: p 
                for p in BiddingProject.objects.only(
                    'source_emall', 'status', 'control_price', 'end_time', 
                    'title', 'root_category', 'sub_category'
                )
            }

        success_count = 0
        skip_count = 0
        error_count = 0

        # =================================================================
        # 4. 循环处理数据
        # =================================================================
        for raw in raw_qs:
            try:
                # --- A. 基础字段清洗 ---
                province = self.parse_province(raw.region)
                if not province: continue

                title = raw.project_title or raw.project_name or "无标题项目"
                mode = 'reverse' if '反拍' in title else 'bidding'
                price = self.convert_price_to_number(raw.total_price_control)
                start = self.parse_time(raw.quote_start_time)
                end = self.parse_time(raw.quote_end_time)
                new_status = self.calc_status(start, end)

                # --- B. 严格分类赋值 (核心修复) ---
                
                # 1. 一级分类：直接取映射表，默认为 goods
                root_cat = root_category_map.get(raw.id, 'goods')

                # 2. 二级分类：取映射表中的中文名，然后转换成代码
                raw_sub_cat_name = sub_category_raw_map.get(raw.id)
                sub_cat = self.map_sub_category(raw_sub_cat_name, root_cat)

                # --- C. 增量比对逻辑 ---
                if not force_update and raw.id in existing_projects:
                    existing = existing_projects[raw.id]
                    
                    # 全字段严格比对
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

                # --- D. 数据库写入 ---
                BiddingProject.objects.update_or_create(
                    source_emall=raw,
                    defaults={
                        'title': title,
                        'province': province,
                        'root_category': root_cat,   # 严格映射
                        'sub_category': sub_cat,     # 严格映射
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
                if error_count <= 5:
                    self.stdout.write(self.style.ERROR(f'ID {raw.id} 同步失败: {e}'))
                continue

        self.stdout.write(self.style.SUCCESS(f'同步完成！更新: {success_count}, 跳过: {skip_count}, 失败: {error_count}'))

    # =================================================================
    # 辅助方法
    # =================================================================

    def map_sub_category(self, c_name, root_cat):
        """
        将 procurement_commodity_category 中的中文分类映射为 bidding 模型的代码
        """
        # 如果一级分类不是物资，或者没有二级分类名称，返回默认
        if not c_name:
            if root_cat == 'service': return 'service_other'
            if root_cat == 'project': return 'project_other' # 假设有这个或者都归为 service_other
            return 'service_other' # 默认兜底

        name = str(c_name).strip()

        # 严格映射逻辑 (物资类7大类)
        # 根据样本数据: "行政办公耗材", "数码家电", "专业设备与工业品"
        if '办公' in name or '耗材' in name:
            return 'office'
        elif '数码' in name or '家电' in name or '电脑' in name:
            return 'digital'
        elif '工业' in name or '设备' in name or '建材' in name:
            return 'industrial'
        elif '清洁' in name or '劳保' in name:
            return 'cleaning'
        elif '食品' in name or '粮油' in name or '超市' in name:
            return 'food'
        elif '体育' in name or '服装' in name or '纺织' in name:
            return 'sports'
        elif '家具' in name:
            # 如果模型里没有 furniture，通常归类到 industrial 或 office，这里假设有或归入 industrial
            return 'industrial' 
        
        return 'service_other'

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