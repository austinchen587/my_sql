# emall_purchasing/views/select_views.py
import redis
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import ProcurementPurchasing
from emall.models import ProcurementEmall
from ..serializers import ProcurementPurchasingSerializer
from .username_utils import get_username_from_request
import logging
import psycopg2

# 👇 [新增] 引入商品品牌模型，用于获取这个采购单下到底有哪些商品需要抓
from bidding.models import ProcurementCommodityBrand 

logger = logging.getLogger(__name__)

# ==============================================================================
# 👇 [新增] Redis 连接配置 (连接你的云端中央大本营)
# ==============================================================================
REDIS_CONFIG = {
    'host': '121.43.77.214', 
    'port': 6379,
    'password': 'austinchen587', 
    'decode_responses': True
}
r_client = redis.Redis(**REDIS_CONFIG)

# 👉 [新增] 云端中央数据库配置
DB_CONFIG = {
    'host': '121.43.77.214',
    'port': 5432,
    'dbname': 'austinchen587_db',
    'user': 'austinchen587',
    'password': 'austinchen587'
}


class ProcurementSelectView(APIView):
    def post(self, request, procurement_id):
        try:
            procurement = ProcurementEmall.objects.get(id=procurement_id)
            current_user = get_username_from_request(request)
            
            purchasing_info, created = ProcurementPurchasing.objects.get_or_create(
                procurement=procurement,
                defaults={'is_selected': True, 'project_owner': current_user}
            )
            
            if not created:
                if purchasing_info.is_selected:
                    purchasing_info.is_selected = False
                    purchasing_info.project_owner = '未分配'  
                else:
                    purchasing_info.is_selected = True
                    purchasing_info.project_owner = current_user  
                purchasing_info.save()
            
            # ==============================================================
            # 🔥 [架构升级] 自动派单 + 同步 Brand 数据到云端大本营！
            # ==============================================================
            if purchasing_info.is_selected:
                try:
                    current_server = request.get_host().split(':')[0]
                    brands = ProcurementCommodityBrand.objects.filter(procurement_id=procurement_id)
                    
                    # 1. 连接云端中央数据库
                    conn = psycopg2.connect(**DB_CONFIG)
                    cur = conn.cursor()
                    
                    # 2. 自动修复云端表结构 (如果缺少 specifications 字段，自动加上)
                    cur.execute("ALTER TABLE procurement_commodity_brand ADD COLUMN IF NOT EXISTS specifications TEXT;")
                    conn.commit()

                    task_count = 0
                    shared_count = 0 # 记录成功白嫖的数量
                    for brand in brands:
                        # 3. 将 Brand 需求数据同步写入云端中央库
                        specs = getattr(brand, 'specifications', '')
                        
                        cur.execute("""
                            INSERT INTO procurement_commodity_brand (id, procurement_id, item_name, specifications)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (id) DO UPDATE SET 
                                procurement_id = EXCLUDED.procurement_id,
                                item_name = EXCLUDED.item_name,
                                specifications = EXCLUDED.specifications;
                        """, (brand.id, str(procurement_id), brand.item_name, specs))
                        
                        # =========================================================
                        # 🔥 [核心修复：SKU 与 AI 结果的跨服共享] 
                        # =========================================================
                        cur.execute("""
                            SELECT item_name, specifications, selected_suppliers, selection_reason, model_used
                            FROM procurement_commodity_result
                            WHERE brand_id = %s AND status = 'completed'
                            LIMIT 1
                        """, (brand.id,))
                        
                        existing_result = cur.fetchone()
                        
                        if existing_result:
                            # 🎯 直接白嫖已有结果！
                            res_item_name, res_specs, res_suppliers, res_reason, res_model = existing_result
                            
                            # 处理 JSON 格式兼容
                            if isinstance(res_suppliers, (dict, list)):
                                res_suppliers_str = json.dumps(res_suppliers, ensure_ascii=False)
                            else:
                                res_suppliers_str = res_suppliers
                                
                            # 为当前服务器写一份 completed 记录，直接触发前端展示
                            cur.execute("""
                                INSERT INTO procurement_commodity_result 
                                (brand_id, server_ip, procurement_id, item_name, specifications, selected_suppliers, selection_reason, model_used, status)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'completed')
                                ON CONFLICT (brand_id, server_ip) DO UPDATE SET 
                                    selected_suppliers = EXCLUDED.selected_suppliers,
                                    selection_reason = EXCLUDED.selection_reason,
                                    status = 'completed';
                            """, (brand.id, current_server, str(procurement_id), res_item_name, res_specs, res_suppliers_str, f"【跨服共享】{res_reason}", res_model))
                            
                            shared_count += 1
                            logger.info(f"🎉 [跨服共享] 发现中央库已有结果！服务器 {current_server} 直接复用 BrandID: {brand.id} 的数据，跳过爬虫！")
                        else:
                            # 没有缓存，老老实实派发给爬虫
                            task_payload = {
                                "brand_id": brand.id,
                                "server_ip": current_server,
                                "item_name": brand.item_name,
                                "key_word": brand.key_word or brand.item_name,
                                "platform": brand.search_platform or "淘宝",
                                "procurement_id": str(procurement_id)
                            }
                            r_client.lpush("crawler_task_queue", json.dumps(task_payload))
                            task_count += 1
                    
                    conn.commit()
                    cur.close()
                    conn.close()
                    
                    logger.info(f"🚀 [自动派单] 项目 {procurement_id} 处理完毕：派发新任务 {task_count} 个，跨服共享 {shared_count} 个！")
                except Exception as e:
                    logger.error(f"❌ [自动派单与同步] 失败: {e}")
            # ==============================================================
            
            return Response({
                'success': True,
                'is_selected': purchasing_info.is_selected,
                'project_owner': purchasing_info.project_owner,
                'message': '选择成功，系统已开始后台自动寻源' if purchasing_info.is_selected else '已取消选择'
            })
            
        except Exception as e:
            logger.error(f"操作失败，错误: {str(e)}")
            return Response({'success': False, 'error': str(e)},status=500)
class ProcurementPurchasingListView(APIView):
    """已选择的采购项目列表"""
    def get(self, request):
        purchasing_list = ProcurementPurchasing.objects.filter(is_selected=True)
        serializer = ProcurementPurchasingSerializer(purchasing_list, many=True)
        return Response(serializer.data)