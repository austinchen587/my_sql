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

# 👉 [新增] 穿透反向代理获取真实前端 IP 的终极函数
def get_real_server_ip(request):
    # 1. 优先尝试 Referer (最可靠，代理一般不改这个)
    # 比如 'http://116.62.86.107:3000/bidding/detail/21873'
    referer = request.META.get('HTTP_REFERER', '')
    if referer:
        return referer.split('://')[-1].split(':')[0].split('/')[0]
    
    # 2. 尝试 Origin 和 X-Forwarded-Host
    origin = request.META.get('HTTP_ORIGIN', '')
    if origin:
        return origin.split('://')[-1].split(':')[0]
    
    xff_host = request.META.get('HTTP_X_FORWARDED_HOST', '')
    if xff_host:
        return xff_host.split(':')[0]
        
    # 3. 兜底
    return request.get_host().split(':')[0]


class ProcurementSelectView(APIView):
    def post(self, request, procurement_id):
        try:
            # 1. 基础业务逻辑：获取采购项目与当前用户
            procurement = ProcurementEmall.objects.get(id=procurement_id)
            current_user = get_username_from_request(request)
            
            purchasing_info, created = ProcurementPurchasing.objects.get_or_create(
                procurement=procurement,
                defaults={'is_selected': True, 'project_owner': current_user}
            )
            
            # 如果不是新创建的，则切换选中状态
            if not created:
                if purchasing_info.is_selected:
                    purchasing_info.is_selected = False
                    purchasing_info.project_owner = '未分配'  
                else:
                    purchasing_info.is_selected = True
                    purchasing_info.project_owner = current_user  
                purchasing_info.save()
            
            # ==============================================================
            # 🔥 [架构升级] 云端预检 + 精准派单逻辑
            # ==============================================================
            if purchasing_info.is_selected:
                try:
                    current_server = get_real_server_ip(request)
                    # 获取该项目下所有的商品需求记录
                    brands = ProcurementCommodityBrand.objects.filter(procurement_id=procurement_id)
                    
                    # 连接云端中央数据库
                    conn = psycopg2.connect(**DB_CONFIG)
                    cur = conn.cursor()

                    task_count = 0
                    shared_count = 0 

                    for brand in brands:
                        # 清洗数据
                        clean_item_name = brand.item_name.strip() if brand.item_name else ""
                        safe_key_word = brand.key_word.strip() if getattr(brand, 'key_word', None) else clean_item_name
                        safe_platform = brand.search_platform.strip() if getattr(brand, 'search_platform', None) else "淘宝"

                        # --- 【核心优化点：复合精准匹配】 ---
                        # 利用 procurement_id + brand_id 复合索引快速定位，不进行全表循环
                        cur.execute("""
                            SELECT status FROM procurement_commodity_result 
                            WHERE procurement_id = %s AND brand_id = %s 
                              AND status IN ('completed', 'synced')
                            LIMIT 1
                        """, (str(procurement_id), brand.id))
                        
                        existing_res = cur.fetchone()

                        if existing_res:
                            # 命中结果：说明该项目的该商品已处理完成，直接复用
                            shared_count += 1
                            logger.info(f"✅ [精准共享] 项目:{procurement_id} | 商品ID:{brand.id} ({clean_item_name}) 已有结果。")
                        else:
                            # 未命中：构建任务负载并下发至 Redis 任务队列
                            task_payload = {
                                "brand_id": brand.id,
                                "procurement_id": str(procurement_id),
                                "server_ip": current_server,
                                "item_name": clean_item_name,
                                "key_word": safe_key_word,
                                "platform": safe_platform
                            }
                            # 推入队列，由 API Worker 监听并执行 Search -> Detail 环节
                            r_client.lpush("crawler_task_queue", json.dumps(task_payload))
                            task_count += 1
                    
                    conn.commit()
                    cur.close()
                    conn.close()
                    
                    logger.info(f"🚀 [派单完成] 项目 {procurement_id}: 新增任务 {task_count} 个，精准复用 {shared_count} 个。")
                except Exception as e:
                    logger.error(f"❌ [云端预检与派单] 失败: {e}")
            # ==============================================================
            
            return Response({
                'success': True,
                'is_selected': purchasing_info.is_selected,
                'project_owner': purchasing_info.project_owner,
                'message': '选择成功，系统已开始后台自动寻源' if purchasing_info.is_selected else '已取消选择'
            })
            
        except Exception as e:
            logger.error(f"操作失败，错误: {str(e)}")
            return Response({'success': False, 'error': str(e)}, status=500)
class ProcurementPurchasingListView(APIView):
    """已选择的采购项目列表"""
    def get(self, request):
        purchasing_list = ProcurementPurchasing.objects.filter(is_selected=True)
        serializer = ProcurementPurchasingSerializer(purchasing_list, many=True)
        return Response(serializer.data)