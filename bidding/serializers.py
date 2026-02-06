import json
import logging
from rest_framework import serializers
from .models import BiddingProject, ProcurementCommodityResult, ProcurementCommodityBrand
from django.utils import timezone
# [新增] 导入 ProcurementPurchasing 模型，注意路径可能需要根据你的实际目录调整
from emall_purchasing.models import ProcurementPurchasing

logger = logging.getLogger(__name__)

class BiddingHallSerializer(serializers.ModelSerializer):
    # [新增] 显式定义 id 字段，将其指向主键 (pk)
    # 这样即使模型里没有 'id' 字段 (比如用了 source_emall 做主键)，也能正常工作
    id = serializers.IntegerField(source='pk', read_only=True)


    price_display = serializers.SerializerMethodField()
    countdown = serializers.SerializerMethodField()
    status_text = serializers.CharField(source='get_status_display', read_only=True)
    
    # [新增] 采购业务字段
    is_selected = serializers.SerializerMethodField()
    project_owner = serializers.SerializerMethodField()
    bidding_status_display = serializers.SerializerMethodField()
    
    requirements = serializers.SerializerMethodField()
    recommendations = serializers.SerializerMethodField()

    # [新增] 获取采购信息的辅助方法
    def get_purchasing_info(self, obj):
        try:
            return obj.source_emall.purchasing_info
        except Exception:
            return None

    # [新增] 增加 raw status 字段
    bidding_status = serializers.SerializerMethodField()

    def get_bidding_status(self, obj):
        info = self.get_purchasing_info(obj)
        return info.bidding_status if info else 'not_started'

    class Meta:
        model = BiddingProject
        fields = [
            'id', 'title', 'province', 'root_category', 'sub_category', 'mode',
            'price_display', 'start_time', 'end_time', 'status', 'status_text',
            'countdown', 'requirements', 'recommendations',
            # [新增] 注册新字段
            'is_selected', 'project_owner', 'bidding_status_display','bidding_status'
        ]

    # --- [新增] 辅助方法：获取关联的采购信息 ---
    def get_purchasing_info(self, obj):
        # obj 是 BiddingProject，关联了 source_emall
        # source_emall 反向关联了 purchasing_info (OneToOneField)
        try:
            return obj.source_emall.purchasing_info
        except Exception:
            return None

    def get_is_selected(self, obj):
        info = self.get_purchasing_info(obj)
        return info.is_selected if info else False

    def get_project_owner(self, obj):
        info = self.get_purchasing_info(obj)
        return info.project_owner if info else '未分配'

    def get_bidding_status_display(self, obj):
        info = self.get_purchasing_info(obj)
        # 获取 choices 的显示文本
        return info.get_bidding_status_display() if info else '未开始'

    # ... (其他原有的 get_price_display 等方法保持不变) ...
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
                        "item_name": item_name, "specifications": spec, "brand": brand_name, "reason": reason, "candidates": candidates
                    })
            elif results.exists():
                for res in results:
                    candidates = []
                    if res.selected_suppliers:
                        try: candidates = json.loads(res.selected_suppliers)
                        except: pass
                    final_list.append({
                        "item_name": res.item_name, "specifications": res.specifications, "reason": res.selection_reason, "candidates": candidates
                    })
        except Exception as e:
            logger.warning(f"获取推荐详情失败: {str(e)}")
            pass
        return final_list