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
    """【新架构适配版】重新寻源接口"""
    brand_id = request.data.get('brand_id')
    new_keyword = request.data.get('new_keyword')
    new_platform = request.data.get('new_platform')
    
    current_server = get_real_server_ip(request)
    
    if not brand_id:
        return Response({'success': False, 'message': '缺少商品ID'}, status=400)

    try:
        # 1. 本地逻辑更新
        brand_obj = ProcurementCommodityBrand.objects.get(id=brand_id)
        if new_keyword: brand_obj.key_word = new_keyword.strip()
        if new_platform: brand_obj.search_platform = new_platform.strip()
        brand_obj.save()

        # 2. 云端大本营同步与状态重置
        try:
            conn = psycopg2.connect(**DB_CONFIG) # 使用 77.214 配置
            cur = conn.cursor()
            
            # A. 确保云端 Brand 信息是最新的（含修改后的关键词）
            specs = getattr(brand_obj, 'specifications', '')
            cur.execute("""
                INSERT INTO procurement_commodity_brand (id, procurement_id, item_name, specifications, key_word, search_platform)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET 
                    key_word = EXCLUDED.key_word,
                    search_platform = EXCLUDED.search_platform,
                    item_name = EXCLUDED.item_name;
            """, (brand_obj.id, str(brand_obj.procurement_id), brand_obj.item_name, specs, brand_obj.key_word, brand_obj.search_platform))
            
            # B. 🔥【关键点】重置云端 Result 状态，确保 Worker 重新执行后同步脚本才会拉取新数据
            cur.execute("""
                UPDATE procurement_commodity_result 
                SET status = 'searching', selection_reason = %s
                WHERE brand_id = %s;
            """, (f"服务器 {current_server} 正在重新寻源中...", brand_id))
            
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            logger.error(f"❌ [云端同步] 重新寻源前置处理失败: {e}")

        # 3. 标准化派发 Redis 任务
        crawler_platform_map = {"京东": "jd", "淘宝": "taobao", "1688": "1688"}
        raw_platform = brand_obj.search_platform or "淘宝"
        target_crawler_platform = crawler_platform_map.get(raw_platform, raw_platform).lower()

        task_payload = {
            "brand_id": brand_id,
            "procurement_id": str(brand_obj.procurement_id),
            "server_ip": current_server, 
            "item_name": brand_obj.item_name,
            "key_word": brand_obj.key_word or brand_obj.item_name,
            "platform": target_crawler_platform
        }
        
        # 将任务投递至队列
        r_client.lpush("crawler_task_queue", json.dumps(task_payload))

        return Response({
            'success': True, 
            'message': f'✅ 已提交重新寻源请求 ({raw_platform}:{brand_obj.key_word})'
        })

    except Exception as e:
        logger.error(f"❌ 重新寻源派单失败: {str(e)}")
        return Response({'success': False, 'message': str(e)}, status=500)

@api_view(['GET'])
@authentication_classes([]) 
@permission_classes([AllowAny])
def get_raw_crawler_data(request):
    """获取爬虫搜索或详情的原数据"""
    brand_id = request.query_params.get('brand_id')
    platform = request.query_params.get('platform')  # 京东, 淘宝, 1688
    data_type = request.query_params.get('type')     # search, detail
    
    if not all([brand_id, platform, data_type]):
        return Response({'error': '缺少必要参数'}, status=400)

    # 1. 映射平台英文名
    platform_map = {"京东": "jd", "淘宝": "taobao", "1688": "1688"}
    p_en = platform_map.get(platform)
    if not p_en: 
        return Response({'error': f'平台 {platform} 不识别'}, status=400)

    # 2. 拼装表名
    table_name = f"procurement_commodity_{p_en}_{data_type}"
    
    try:
        # 使用你文件中已定义的 DB_CONFIG 连接
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # 查询该 brand_id 下的所有原记录
        query = f"SELECT * FROM {table_name} WHERE brand_id = %s ORDER BY id DESC"
        cur.execute(query, (brand_id,))
        
        # 获取列名并组装为字典列表
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        result = [dict(zip(columns, row)) for row in rows]
        
        cur.close()
        conn.close()
        return Response({'success': True, 'data': result})
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)