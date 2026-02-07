import json
import logging
from rest_framework import serializers
from .models import BiddingProject, ProcurementCommodityResult, ProcurementCommodityBrand
from django.utils import timezone
from emall_purchasing.models import ProcurementPurchasing

logger = logging.getLogger(__name__)

class BiddingHallSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='pk', read_only=True)

    price_display = serializers.SerializerMethodField()
    countdown = serializers.SerializerMethodField()
    status_text = serializers.CharField(source='get_status_display', read_only=True)
    
    is_selected = serializers.SerializerMethodField()
    project_owner = serializers.SerializerMethodField()
    bidding_status_display = serializers.SerializerMethodField()
    bidding_status = serializers.SerializerMethodField()
    
    requirements = serializers.SerializerMethodField()
    recommendations = serializers.SerializerMethodField()

    class Meta:
        model = BiddingProject
        fields = [
            'id', 'title', 'province', 'root_category', 'sub_category', 'mode',
            'price_display', 'start_time', 'end_time', 'status', 'status_text',
            'countdown', 'requirements', 'recommendations',
            'is_selected', 'project_owner', 'bidding_status_display', 'bidding_status'
        ]

    # ... (get_purchasing_info, get_is_selected 等辅助方法保持不变，省略以节省篇幅) ...
    def get_purchasing_info(self, obj):
        try: return obj.source_emall.purchasing_info
        except: return None
    def get_is_selected(self, obj):
        info = self.get_purchasing_info(obj)
        return info.is_selected if info else False
    def get_project_owner(self, obj):
        info = self.get_purchasing_info(obj)
        return info.project_owner if info else '未分配'
    def get_bidding_status_display(self, obj):
        info = self.get_purchasing_info(obj)
        return info.get_bidding_status_display() if info else '未开始'
    def get_bidding_status(self, obj):
        info = self.get_purchasing_info(obj)
        return info.bidding_status if info else 'not_started'
    def get_price_display(self, obj):
        if not obj.control_price: return "详见公告"
        return f"{obj.control_price/10000:.2f}万元" if obj.control_price >= 10000 else f"{obj.control_price:.2f}元"
    def get_countdown(self, obj):
        now = timezone.now()
        target = obj.end_time if (obj.start_time and now >= obj.start_time) else obj.start_time
        if not target or now > target: return 0
        return int((target - now).total_seconds())
    def get_requirements(self, obj):
        if self.context.get('view_type') == 'list': return None
        try:
            s = obj.source_emall 
            raw_date = getattr(s, 'publish_date', None)
            pub_date = raw_date.strftime('%Y-%m-%d') if hasattr(raw_date, 'strftime') else (str(raw_date) if raw_date else '')

            # [辅助函数] 解析 Postgres 数组字符串 "{内容1, 内容2}"
            def parse_pg_array(text):
                if not text or text == '{}': return []
                # 去除首尾的花括号
                content = str(text).strip('{}')
                if not content: return []
                
                # 针对被双引号包裹的长文本 (例如 "{""第一条...""}")
                if content.startswith('"') and content.endswith('"'):
                    # 去除首尾引号，并将双引号转义为单引号
                    return [content[1:-1].replace('""', '"')]
                
                # 普通情况按逗号分割
                return [item.strip() for item in content.split(',')]

            # 1. 解析附件与链接
            raw_files = getattr(s, 'download_files', '')
            raw_links = getattr(s, 'related_links', '')
            
            # 2. [核心新增] 解析商务字段
            # 对应数据库中的 business_items 和 business_requirements 列
            raw_biz_items = getattr(s, 'business_items', '')
            raw_biz_reqs = getattr(s, 'business_requirements', '')

            return {
                "params": getattr(s, 'parameter_requirements', ''),
                "brands": getattr(s, 'suggested_brands', ''),
                "quantities": getattr(s, 'purchase_quantities', ''),
                "project_code": getattr(s, 'project_number', ''),
                "publish_date": pub_date, 
                "purchaser": getattr(s, 'purchasing_unit', ''),
                "url": getattr(s, 'url', ''),
                
                # 附件列表
                "file_names": parse_pg_array(raw_files), 
                "file_urls": parse_pg_array(raw_links),

                # [核心新增] 返回解析后的商务数据列表
                "business_items": parse_pg_array(raw_biz_items),
                "business_reqs": parse_pg_array(raw_biz_reqs)
            }
        except Exception as e:
            logger.error(f"解析需求字段失败: {e}")
            return None

    # [核心修复部分]
    def get_recommendations(self, obj):
        if self.context.get('view_type') == 'list': return None
        final_list = []
        try:
            pid = str(obj.pk)
            
            # 1. 获取两张表的数据
            brands = ProcurementCommodityBrand.objects.filter(procurement_id=pid)
            results = ProcurementCommodityResult.objects.filter(procurement_id=pid)
            
            # 2. 建立索引映射
            # 映射 A: ID -> Result (优先使用)
            id_map = {r.brand_id: r for r in results if r.brand_id is not None}
            # 映射 B: 名称 -> Result (兜底备用)
            name_map = {r.item_name: r for r in results if r.item_name}
            
            # 记录已使用的 result_id，防止重复展示
            used_result_ids = set()

            # --- 阶段一：遍历需求清单 (Brand) ---
            if brands.exists():
                for b in brands:
                    # [双重匹配策略]
                    # 第一步：尝试 ID 严格匹配 (基于你的数据库验证)
                    res = id_map.get(b.id)
                    
                    # 第二步：如果 ID 没匹配上，尝试名称匹配 (容错兜底)
                    if not res and b.item_name:
                        res = name_map.get(b.item_name)
                    
                    # 初始化基础信息
                    item_name = b.item_name
                    spec = b.specifications
                    brand_name = b.suggested_brand 
                    candidates = []
                    reason = "AI 正在分析中..." # 默认文案优化
                    
                    if res:
                        # 标记此 Result 已被成功匹配
                        used_result_ids.add(res.id)
                        
                        # 融合数据：优先用 Result 的数据覆盖
                        item_name = res.item_name or item_name
                        spec = res.specifications or spec
                        reason = res.selection_reason
                        
                        # [核心修复] JSON 数据清洗
                        if res.selected_suppliers:
                            raw_str = res.selected_suppliers
                            try:
                                # 尝试直接解析
                                candidates = json.loads(raw_str)
                            except:
                                try:
                                    # 针对 CSV 格式双引号进行清洗: "" -> "
                                    clean_str = raw_str.replace('""', '"')
                                    # 去除首尾多余的引号 (如果是字符串包裹)
                                    if clean_str.startswith('"') and clean_str.endswith('"'):
                                        clean_str = clean_str[1:-1]
                                    candidates = json.loads(clean_str)
                                except Exception as e:
                                    logger.error(f"JSON清洗失败 (ID:{res.id}): {e}")
                                    candidates = []
                    
                    final_list.append({
                        "item_name": item_name, 
                        "specifications": spec, 
                        "brand": brand_name, 
                        "reason": reason, 
                        "candidates": candidates,
                        # 补全 Brand 字段
                        "quantity": getattr(b, 'quantity', None),
                        "unit": getattr(b, 'unit', None),
                        "key_word": getattr(b, 'key_word', None),
                        "search_platform": getattr(b, 'search_platform', None),
                        "notes": getattr(b, 'notes', None)
                    })

            # --- 阶段二：处理“孤儿”结果 (Result) ---
            # 只有那些完全没有匹配上 Brand 的 Result 才会在这里显示
            for res in results:
                if res.id not in used_result_ids:
                    candidates = []
                    if res.selected_suppliers:
                        try:
                            # 同样的清洗逻辑
                            clean_str = res.selected_suppliers.replace('""', '"')
                            if clean_str.startswith('"') and clean_str.endswith('"'):
                                clean_str = clean_str[1:-1]
                            candidates = json.loads(clean_str)
                        except:
                            candidates = []
                    
                    final_list.append({
                        "item_name": res.item_name, 
                        "specifications": res.specifications, 
                        "brand": "未知(原始清单丢失)", 
                        "reason": res.selection_reason, 
                        "candidates": candidates,
                        "quantity": "-", "unit": "-", "key_word": "-", "search_platform": "-", "notes": "关联ID断裂"
                    })

        except Exception as e:
            logger.warning(f"获取推荐详情失败: {str(e)}")
            return []
            
        return final_list