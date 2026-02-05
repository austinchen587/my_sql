import json
import logging
from rest_framework import serializers
from .models import BiddingProject, ProcurementCommodityResult, ProcurementCommodityBrand 
from django.utils import timezone

logger = logging.getLogger(__name__)

class BiddingHallSerializer(serializers.ModelSerializer):
    # [核心修复] 显式把 pk 映射为 id 字段返回给前端
    id = serializers.IntegerField(source='pk', read_only=True)
    
    price_display = serializers.SerializerMethodField()
    countdown = serializers.SerializerMethodField()
    status_text = serializers.CharField(source='get_status_display', read_only=True)
    
    requirements = serializers.SerializerMethodField()
    recommendations = serializers.SerializerMethodField()

    class Meta:
        model = BiddingProject
        fields = [
            'id', 'title', 'province', 'root_category', 'sub_category', 'mode',
            'price_display', 'start_time', 'end_time', 'status', 'status_text',
            'countdown', 'requirements', 'recommendations'
        ]

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
            # 访问关联对象
            s = obj.source_emall 
            raw_date = getattr(s, 'publish_date', None)
            pub_date = raw_date.strftime('%Y-%m-%d') if hasattr(raw_date, 'strftime') else (str(raw_date) if raw_date else '')
            
            return {
                "params": getattr(s, 'parameter_requirements', ''),
                "brands": getattr(s, 'suggested_brands', ''),
                "quantities": getattr(s, 'purchase_quantities', ''),
                "project_code": getattr(s, 'project_number', ''),
                "publish_date": pub_date, 
                "purchaser": getattr(s, 'purchasing_unit', ''),
                "url": getattr(s, 'url', '')
            }
        except Exception as e:
            logger.error(f"获取需求失败: {e}")
            return None

    def get_recommendations(self, obj):
        if self.context.get('view_type') == 'list': return None
        
        final_list = []
        try:
            pid = str(obj.pk)
            
            brands = ProcurementCommodityBrand.objects.filter(procurement_id=pid)
            results = ProcurementCommodityResult.objects.filter(procurement_id=pid)
            result_map = {r.brand_id: r for r in results}

            if brands.exists():
                for b in brands:
                    res = result_map.get(b.id)
                    item_name = b.item_name
                    spec = b.specifications
                    # [新增 1] 获取建议品牌
                    brand_name = b.suggested_brand 
                    
                    candidates = []
                    reason = "AI 尚未分析此条目"
                    
                    if res:
                        item_name = res.item_name or item_name
                        spec = res.specifications or spec
                        reason = res.selection_reason
                        if res.selected_suppliers:
                            try: candidates = json.loads(res.selected_suppliers)
                            except: pass
                            
                    final_list.append({
                        "item_name": item_name,
                        "specifications": spec,
                        "brand": brand_name,   # [新增 2] 输出到 JSON
                        "reason": reason,
                        "candidates": candidates
                    })
            
            elif results.exists():
                for res in results:
                    candidates = []
                    if res.selected_suppliers:
                        try: candidates = json.loads(res.selected_suppliers)
                        except: pass
                    final_list.append({
                        "item_name": res.item_name,
                        "specifications": res.specifications,
                        "reason": res.selection_reason,
                        "candidates": candidates
                    })

        except Exception as e:
            logger.warning(f"获取推荐详情失败: {str(e)}")
            pass
            
        return final_list