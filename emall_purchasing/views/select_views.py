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
                    # 🛡️ 使用我们新写的穿透函数获取真实 IP
                    current_server = get_real_server_ip(request)
                    brands = ProcurementCommodityBrand.objects.filter(procurement_id=procurement_id)
                    
                    # 1. 连接云端中央数据库
                    conn = psycopg2.connect(**DB_CONFIG)
                    cur = conn.cursor()
                    
                    # 2. 自动修复云端表结构 (如果缺少 specifications 字段，自动加上)
                    cur.execute("ALTER TABLE procurement_commodity_brand ADD COLUMN IF NOT EXISTS specifications TEXT;")
                    # 👇 加上这两行“免死金牌”，确保存储万无一失
                    cur.execute("ALTER TABLE procurement_commodity_brand ADD COLUMN IF NOT EXISTS key_word VARCHAR(255);")
                    cur.execute("ALTER TABLE procurement_commodity_brand ADD COLUMN IF NOT EXISTS search_platform VARCHAR(50);")
                    conn.commit()

                    task_count = 0
                    shared_count = 0 # 记录成功白嫖的数量
                    for brand in brands:
                        # 👉 1. 彻底清理脏数据（去除两端空格，防雷）
                        clean_item_name = brand.item_name.strip() if brand.item_name else ""
                        clean_key_word = brand.key_word.strip() if getattr(brand, 'key_word', None) else ""
                        clean_platform = brand.search_platform.strip() if getattr(brand, 'search_platform', None) else ""
                        
                        # 兜底默认值
                        safe_key_word = clean_key_word if clean_key_word else (clean_item_name or "")
                        safe_platform = clean_platform if clean_platform else "淘宝"
                        specs = getattr(brand, 'specifications', '')

                        # 3. 将 Brand 需求数据同步写入云端中央库 (附带完整字段)
                        cur.execute("""
                            INSERT INTO procurement_commodity_brand 
                            (id, procurement_id, item_name, specifications, key_word, search_platform)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (id) DO UPDATE SET 
                                procurement_id = EXCLUDED.procurement_id,
                                item_name = EXCLUDED.item_name,
                                specifications = EXCLUDED.specifications,
                                key_word = EXCLUDED.key_word,
                                search_platform = EXCLUDED.search_platform;
                        """, (brand.id, str(procurement_id), clean_item_name, specs, safe_key_word, safe_platform))
                        
                        # =========================================================
                        # 🔥 修复：优先复用有商品的记录！
                        # =========================================================
                        cur.execute("""
                            SELECT item_name, specifications, selected_suppliers, selection_reason, model_used, status
                            FROM procurement_commodity_result
                            WHERE item_name = %s 
                              AND procurement_id != %s  -- 👉 必须是别的项目的历史经验！不能抄自己！
                              AND status IN ('completed', 'synced') -- 不要抄失败的
                              AND model_used != 'System_Success'    -- 👉 坚决不复用系统占位符数据！
                              AND length(selected_suppliers::text) > 15 -- 确保里面真的有商品数组
                            ORDER BY id DESC
                            LIMIT 1
                        """, (clean_item_name, str(procurement_id)))
                        
                        # 👉 注意：这里只能有一句 fetchone()！删除了你多余的那句。
                        existing_result = cur.fetchone() 
                        
                        if existing_result:
                            res_item_name, res_specs, res_suppliers, res_reason, res_model, res_status = existing_result
                            
                            # 🛡️ 终极防御：先尝试解析再重新序列化，确保一定是双引号标准 JSON
                            try:
                                if isinstance(res_suppliers, str):
                                    import ast
                                    if "'" in res_suppliers and '"' not in res_suppliers:
                                        res_suppliers = ast.literal_eval(res_suppliers)
                                    else:
                                        res_suppliers = json.loads(res_suppliers)
                                
                                res_suppliers_str = json.dumps(res_suppliers, ensure_ascii=False)
                            except Exception:
                                res_suppliers_str = '[]'
                                
                            cur.execute("""
                                INSERT INTO procurement_commodity_result 
                                (brand_id, server_ip, procurement_id, item_name, specifications, selected_suppliers, selection_reason, model_used, status)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (brand_id, server_ip) DO UPDATE SET 
                                    selected_suppliers = EXCLUDED.selected_suppliers,
                                    selection_reason = EXCLUDED.selection_reason,
                                    status = EXCLUDED.status;
                            """, (brand.id, current_server, str(procurement_id), res_item_name, res_specs, res_suppliers_str, f"【跨服共享】{res_reason}", res_model, 'completed')) 
                            
                            shared_count += 1
                            logger.info(f"🎉 [跨服共享] 发现云端已有 {clean_item_name} 的结果(状态:{res_status})！服务器 {current_server} 瞬间复用！")
                        else:
                            # 👉 4. 没有缓存，老老实实派发给爬虫 (使用洗净的安全数据)
                            task_payload = {
                                "brand_id": brand.id,
                                "server_ip": current_server,
                                "item_name": clean_item_name,
                                "key_word": safe_key_word,    # 👈 修正为清洗后的兜底变量
                                "platform": safe_platform,    # 👈 修正为清洗后的兜底变量
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