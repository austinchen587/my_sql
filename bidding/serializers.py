import json
import logging
from rest_framework import serializers
from .models import BiddingProject, ProcurementCommodityResult, ProcurementCommodityBrand
from django.utils import timezone
from emall_purchasing.models import ProcurementPurchasing
from rest_framework import serializers

logger = logging.getLogger(__name__)

class BiddingHallSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='pk', read_only=True)

    # 备注相关字段
    latest_remark_content = serializers.CharField(read_only=True)
    latest_remark_by = serializers.CharField(read_only=True)
    latest_remark_at = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M')

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
            'is_selected', 'project_owner', 'bidding_status_display', 'bidding_status',
            'latest_remark_content', 'latest_remark_by', 'latest_remark_at'
        ]

    # ... (辅助方法保持不变) ...
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

    # [核心修改] get_requirements 方法
    def get_requirements(self, obj):
        if self.context.get('view_type') == 'list': return None
        try:
            s = obj.source_emall 
            raw_date = getattr(s, 'publish_date', None)
            pub_date = raw_date.strftime('%Y-%m-%d') if hasattr(raw_date, 'strftime') else (str(raw_date) if raw_date else '')

            # 解析函数 (包含之前的修复：去除多余引号)
            def parse_pg_array(text):
                if not text: return []
                text_str = str(text).strip()
                text_str = text_str.strip("'\"") # 去除首尾引号
                if text_str == '{}' or text_str == '[]': return []
                
                content = text_str.strip('{}[]')
                if not content: return []
                
                result = []
                for item in content.split(','):
                    item = item.strip()
                    if (item.startswith('"') and item.endswith('"')) or \
                       (item.startswith("'") and item.endswith("'")):
                        item = item[1:-1]
                    item = item.replace('""', '"')
                    item = item.strip("[]") 
                    if item:
                        result.append(item)
                return result

            # 1. 获取原始数据
            raw_files = getattr(s, 'download_files', '')
            raw_links = getattr(s, 'related_links', '')
            
            # 2. 解析为列表
            parsed_names = parse_pg_array(raw_files)
            parsed_urls = parse_pg_array(raw_links)
            
            # 3. [新增] 根据 URL 去重
            unique_names = []
            unique_urls = []
            seen_urls = set()
            
            # 取两者较短的长度，确保配对安全
            safe_len = min(len(parsed_names), len(parsed_urls))
            
            for i in range(safe_len):
                url = parsed_urls[i]
                name = parsed_names[i]
                
                # 如果这个 URL 还没出现过，则添加
                if url not in seen_urls:
                    seen_urls.add(url)
                    unique_names.append(name)
                    unique_urls.append(url)

            # 4. 解析商务字段
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
                
                # 返回去重后的列表
                "file_names": unique_names, 
                "file_urls": unique_urls,

                "business_items": parse_pg_array(raw_biz_items),
                "business_reqs": parse_pg_array(raw_biz_reqs)
            }
        except Exception as e:
            logger.error(f"解析需求字段失败: {e}")
            return None

    def get_recommendations(self, obj):
        if self.context.get('view_type') == 'list': return None
        final_list = []
        try:
            # 1. 获取 ID
            source_id = getattr(obj, 'source_emall_id', None)
            if not source_id:
                return []

            # 2. 先查出所有的 Brands (商品清单)
            brands = ProcurementCommodityBrand.objects.filter(procurement_id=source_id)
            
            # 3. [核心修复] 收集所有 Brand IDs，直接用 IDs 去查 Result
            # 不再使用 results = ProcurementCommodityResult.objects.filter(procurement_id=source_id)
            brand_ids = list(brands.values_list('id', flat=True))
            
            # 使用 brand_id__in 进行批量查询
            results = ProcurementCommodityResult.objects.filter(brand_id__in=brand_ids)

            # [调试日志] 看看这就对了
            print(f"\033[93m[DEBUG] ID={source_id} | Brands数量={len(brand_ids)} | 关联的Results数量={results.count()}\033[0m")

            # 4. 建立映射 (后续逻辑保持不变)
            id_map = {r.brand_id: r for r in results if r.brand_id is not None}
            name_map = {r.item_name: r for r in results if r.item_name}
            used_result_ids = set()

            if brands.exists():
                for b in brands:
                    # 优先通过 ID 匹配
                    res = id_map.get(b.id)
                    # 兜底通过名称匹配
                    if not res and b.item_name:
                        res = name_map.get(b.item_name)
                    
                    item_name = b.item_name
                    spec = b.specifications
                    brand_name = b.suggested_brand 
                    candidates = []
                    reason = "AI 正在分析中..."
                    
                    if res:
                        used_result_ids.add(res.id)
                        item_name = res.item_name or item_name
                        spec = res.specifications or spec
                        reason = res.selection_reason
                        
                        if res.selected_suppliers:
                            raw_str = res.selected_suppliers
                            try:
                                clean_str = raw_str.replace('""', '"')
                                if clean_str.startswith('"') and clean_str.endswith('"'):
                                    clean_str = clean_str[1:-1]
                                candidates = json.loads(clean_str)
                            except:
                                try:
                                    # 再次尝试修复常见的 JSON 格式错误
                                    import ast
                                    candidates = ast.literal_eval(raw_str)
                                except:
                                    candidates = []
                    
                    final_list.append({
                        "item_name": item_name, 
                        "specifications": spec, 
                        "brand": brand_name, 
                        "reason": reason, 
                        "candidates": candidates,
                        "quantity": getattr(b, 'quantity', None),
                        "unit": getattr(b, 'unit', None),
                        "key_word": getattr(b, 'key_word', None),
                        "search_platform": getattr(b, 'search_platform', None),
                        "notes": getattr(b, 'notes', None)
                    })
            
            # (可选) 处理孤儿 Result 的逻辑保持不变...

        except Exception as e:
            logger.warning(f"获取推荐详情失败: {str(e)}")
            return []
            
        return final_list