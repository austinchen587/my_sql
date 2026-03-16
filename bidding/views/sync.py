# D:\code\web_sys\my_sql\bidding\views\sync.py
import threading
import logging
import json
import redis 
import psycopg2  # 👉 [新增] 用于直连云端数据库同步数据
from django.core.management import call_command
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from ..models import ProcurementCommodityResult, ProcurementCommodityBrand

logger = logging.getLogger(__name__)

# ==============================================================================
# 🔥 [分布式改造] Redis 与 云端数据库 连接配置
# ==============================================================================
REDIS_CONFIG = {
    'host': '121.43.77.214', 
    'port': 6379,
    'password': 'austinchen587', 
    'decode_responses': True
}
r_client = redis.Redis(**REDIS_CONFIG)

# 👉 [新增] 云端中央大本营数据库配置
DB_CONFIG = {
    'host': '121.43.77.214',
    'port': 5432,
    'dbname': 'austinchen587_db',
    'user': 'austinchen587',
    'password': 'austinchen587'
}

def get_real_server_ip(request):
    referer = request.META.get('HTTP_REFERER', '')
    if referer:
        return referer.split('://')[-1].split(':')[0].split('/')[0]
    origin = request.META.get('HTTP_ORIGIN', '')
    if origin:
        return origin.split('://')[-1].split(':')[0]
    xff_host = request.META.get('HTTP_X_FORWARDED_HOST', '')
    if xff_host:
        return xff_host.split(':')[0]
    return request.get_host().split(':')[0]





@api_view(['POST'])
@authentication_classes([]) 
@permission_classes([AllowAny])
def sync_province_data(request):
    """触发后台同步任务的接口"""
    province = request.data.get('province')
    if not province:
        return Response({'success': False, 'message': '缺少 province 参数'}, status=400)

    def run_sync_command():
        try:
            print(f"🚀 [后台任务] 开始同步省份数据: {province}...")
            call_command('sync_bidding', province=province)
            print(f"✅ [后台任务] 省份 {province} 同步完成")
        except Exception as e:
            print(f"❌ [后台任务] 同步失败: {e}")

    thread = threading.Thread(target=run_sync_command, daemon=True)
    thread.start()
    
    return Response({
        'success': True,
        'message': f'已成功触发 {province} 地区的数据同步任务'
    })


@api_view(['POST'])
@authentication_classes([]) 
@permission_classes([AllowAny])
def retry_single_item(request):
    """【修复版】重新寻源接口"""
    brand_id = request.data.get('brand_id')
    new_keyword = request.data.get('new_keyword')
    new_platform = request.data.get('new_platform')
    
    # 🛡️ 使用强力穿透函数
    current_server = get_real_server_ip(request)
    
    if not brand_id:
        return Response({'success': False, 'message': '缺少商品ID'}, status=400)

    try:
        brand_obj = ProcurementCommodityBrand.objects.get(id=brand_id)
        if new_keyword or new_platform:
            if new_keyword: brand_obj.key_word = new_keyword
            if new_platform: brand_obj.search_platform = new_platform
            brand_obj.save()

        # 👉 [修复 1] 移除 exclude(server_ip=...)
        existing_success = ProcurementCommodityResult.objects.filter(
            brand_id=brand_id, 
            status='completed'
        ).first()

        if existing_success and not new_keyword:
            # 👉 [修复 2] 移除 server_ip=current_server
            ProcurementCommodityResult.objects.update_or_create(
                brand_id=brand_id,
                defaults={
                    'item_name': existing_success.item_name,
                    'specifications': existing_success.specifications,
                    'selected_suppliers': existing_success.selected_suppliers,
                    'selection_reason': f"直接复用已有的同步结果",
                    'model_used': existing_success.model_used,
                    'status': 'completed'
                }
            )
            return Response({'success': True, 'message': '✅ 已直接复用抓取结果'})

        # 👉 [修复 3] 移除 server_ip=current_server
        ProcurementCommodityResult.objects.update_or_create(
            brand_id=brand_id,
            defaults={
                'status': 'retry',
                'selection_reason': f'服务器 {current_server} 正在重新寻源中...',
                'item_name': brand_obj.item_name
            }
        )

        # === 后面云端同步和 Redis 派发的代码保持不变 ===
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("ALTER TABLE procurement_commodity_brand ADD COLUMN IF NOT EXISTS specifications TEXT;")
            conn.commit()
            
            specs = getattr(brand_obj, 'specifications', '')
            cur.execute("""
                INSERT INTO procurement_commodity_brand (id, procurement_id, item_name, specifications)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET 
                    item_name = EXCLUDED.item_name,
                    specifications = EXCLUDED.specifications;
            """, (brand_obj.id, str(brand_obj.procurement_id), brand_obj.item_name, specs))
            
            conn.commit()
            cur.close()
            conn.close()
        # === 前面云端 PostgreSQL 同步的代码保持不变 ===
        except Exception as e:
            logger.error(f"❌ [云端同步] 同步单条商品需求失败: {e}")

        # 👇 [核心修复点]：增加平台标识中英转换字典
        # 爬虫脚本通常只能识别英文字符串，在这里做一层翻译
        crawler_platform_map = {
            "京东": "jd",
            "淘宝": "taobao",
            "1688": "1688"
        }
        
        # 获取数据库里保存的平台名称（此时是中文），默认 fallback 到 'taobao'
        raw_platform = brand_obj.search_platform or "淘宝"
        # 转换成爬虫能认识的英文格式
        target_crawler_platform = crawler_platform_map.get(raw_platform, raw_platform)

        task_payload = {
            "brand_id": brand_id,
            "server_ip": current_server, 
            "item_name": brand_obj.item_name,
            "key_word": brand_obj.key_word or brand_obj.item_name,
            "platform": target_crawler_platform,  # 👉 传给爬虫的是 'jd' / 'taobao' / '1688'
            "procurement_id": brand_obj.procurement_id
        }
        r_client.lpush("crawler_task_queue", json.dumps(task_payload))

        return Response({'success': True, 'message': f'✅ 任务已提交'})

    except Exception as e:
        logger.error(f"❌ 派单失败: {str(e)}")
        return Response({'success': False, 'message': str(e)}, status=500)