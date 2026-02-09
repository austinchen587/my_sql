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
    help = '将 emall 的原始数据清洗并同步到 bidding 表 (支持增量更新)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--province',
            type=str,
            help='指定同步的省份代码 (JX, HN, AH, ZJ, XJ)',
        )
        # [新增] 强制全量更新参数
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制全量更新所有数据',
        )

    def handle(self, *args, **options):
        target_province = options.get('province')
        force_update = options.get('force') # 获取是否强制更新

        # 1. 预加载分类数据
        self.stdout.write("正在预加载分类数据...")
        category_map = {}
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT record_id, category FROM procurement_emall_category")
                rows = cursor.fetchall()
                for r_id, cat in rows:
                    category_map[r_id] = cat
        except Exception:
            pass

        # 2. 查询原始数据
        raw_qs = ProcurementEmall.objects.all()

        if target_province:
            prov_map = {'JX': '江西', 'HN': '湖南', 'AH': '安徽', 'ZJ': '浙江', 'XJ': '新疆'}
            region_keyword = prov_map.get(target_province)
            if region_keyword:
                self.stdout.write(f"正在执行增量同步，目标区域：{region_keyword}...")
                raw_qs = raw_qs.filter(region__contains=region_keyword)

        total = raw_qs.count()
        self.stdout.write(f"扫描到 {total} 条原始数据，开始增量同步...")

        success_count = 0
        skip_count = 0
        error_count = 0
        
        # 批量预加载已存在的 BiddingProject，减少数据库查询
        #以此 id 为 key，存储 (updated_at, status) 等关键信息用于比对
        existing_projects = {}
        if not force_update:
            # 只查询必要的字段
            existing_projects = {
                p.source_emall_id: p 
                for p in BiddingProject.objects.only('source_emall', 'status', 'control_price', 'end_time')
            }

        for raw in raw_qs:
            try:
                # --- 提取与清洗 (保持原有逻辑) ---
                province = self.parse_province(raw.region)
                if not province: continue

                title = raw.project_title or raw.project_name or "无标题项目"
                mode = 'reverse' if '反拍' in title else 'bidding'
                price = self.convert_price_to_number(raw.total_price_control)
                start = self.parse_time(raw.quote_start_time)
                end = self.parse_time(raw.quote_end_time)
                new_status = self.calc_status(start, end)

                # --- 增量比对逻辑 ---
                if not force_update and raw.id in existing_projects:
                    existing = existing_projects[raw.id]
                    
                    # 检查关键字段是否有变化
                    # 1. 状态是否变化 (例如时间流逝导致状态变更)
                    status_changed = existing.status != new_status
                    # 2. 价格是否变化
                    price_changed = existing.control_price != price
                    # 3. 结束时间是否变化
                    end_time_changed = existing.end_time != end
                    
                    # 如果没有任何关键变化，则跳过
                    if not (status_changed or price_changed or end_time_changed):
                        skip_count += 1
                        continue

                # --- 确定分类 (保持原有逻辑) ---
                db_cat = category_map.get(raw.id)
                if db_cat in ['goods', 'project', 'service']:
                    root_cat = db_cat
                else:
                    if any(k in title for k in ['工程', '施工', '改造', '修缮', '建设', '安装', '装修', '整治']):
                        root_cat = 'project'
                    elif any(k in title for k in ['服务', '维保', '检测', '租赁', '运维', '保养', '外包', '物业']):
                        root_cat = 'service'
                    else:
                        root_cat = 'goods'

                sub_cat = 'service_other'
                title_search = title 
                if any(k in title_search for k in ['办公', '纸', '墨']): sub_cat = 'office'
                elif any(k in title_search for k in ['清洁', '洗', '扫']): sub_cat = 'cleaning'
                elif any(k in title_search for k in ['电脑', '数码', '屏', '显']): sub_cat = 'digital'
                elif any(k in title_search for k in ['球', '服', '体育']): sub_cat = 'sports'
                elif any(k in title_search for k in ['工', '机', '泵', '阀', '梯', '设施']): sub_cat = 'industrial'
                elif any(k in title_search for k in ['食', '水', '油', '米']): sub_cat = 'food'

                # --- 执行更新或插入 ---
                BiddingProject.objects.update_or_create(
                    source_emall=raw,
                    defaults={
                        'title': title,
                        'province': province,
                        'root_category': root_cat,
                        'sub_category': sub_cat,
                        'mode': mode,
                        'control_price': price,
                        'start_time': start,
                        'end_time': end,
                        'status': new_status
                    }
                )
                success_count += 1
                if success_count % 50 == 0: # 降低打印频率
                    self.stdout.write(f"已更新 {success_count} 条...")

            except Exception as e:
                error_count += 1
                if error_count <= 5:
                    self.stdout.write(self.style.ERROR(f'ID {raw.id} 同步失败: {e}'))
                continue

        self.stdout.write(self.style.SUCCESS(f'同步完成！更新: {success_count}, 跳过: {skip_count}, 失败: {error_count}'))

    # ... (保持原有的辅助函数 parse_province, convert_price_to_number, parse_time, calc_status 不变) ...
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