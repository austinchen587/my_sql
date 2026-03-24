# coding:utf-8
import redis
import json
import psycopg2
import requests
import logging
import time  
from psycopg2.extras import Json

# ==========================================
# 日志配置
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [Worker] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

DB_CONFIG = {'host': '121.43.77.214', 'port': 5432, 'dbname': 'austinchen587_db', 'user': 'austinchen587', 'password': 'austinchen587'}
REDIS_CONFIG = {'host': '121.43.77.214', 'port': 6379, 'password': 'austinchen587', 'decode_responses': True}
API_KEY = "t3970966868"
API_SECRET = "6868cdc9"

def process_search(task, r_client):
    """【第一棒】负责全网搜索大名单"""
    b_id = task.get('brand_id')
    p_id = task.get('procurement_id')
    s_ip = task.get('server_ip', 'unknown')
    i_name = task.get('item_name', '未知商品')
    kw = task.get('key_word', '')
    platform_raw = task.get('platform', '').lower()
    
    # 👉 【核心修复】：动态判定平台与匹配的 API 接口
    if 'jd' in platform_raw or '京东' in platform_raw:
        plat = 'jd'
        search_api = 'item_search_pro'  # 京东专属 Pro 接口
    elif '1688' in platform_raw:
        plat = '1688'
        search_api = 'item_search'      # 1688 基础接口
    else:
        plat = 'taobao'
        search_api = 'item_search'      # 淘宝基础接口
    
    # 强制把平台标识规范化后塞回任务包，方便传给后面的详情抓取
    task['platform'] = plat 
        
    logger.info(f"🚀 [阶段1: 搜索] BrandID: {b_id} | 商品: {i_name} | 平台: {plat} | 关键词: '{kw}'")
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    try:
        # 使用动态拼接的 search_api
        search_url = f"https://api-gw.onebound.cn/{plat}/{search_api}/"
        logger.info(f"  👉 正在调用 API: {search_url}")
        
        max_retries = 5
        s_res = None
        error_code = None
        
        for attempt in range(1, max_retries + 1):
            try:
                if attempt > 1: logger.info(f"    🔄 正在进行第 {attempt}/{max_retries} 次重试...")
                response = requests.get(search_url, params={"key": API_KEY, "secret": API_SECRET, "q": kw}, timeout=20)
                s_res = response.json()
                error_code = s_res.get("error_code")
                if error_code == "0000": break
                else: logger.warning(f"    ⚠️ 第 {attempt} 次尝试失败: {s_res.get('reason')}")
            except Exception as e:
                logger.warning(f"    ⚠️ 第 {attempt} 次尝试发生网络异常: {e}")
            if attempt < max_retries: time.sleep(3)

        if error_code == "0000" and s_res:
            items = s_res.get("items", {}).get("item", [])
            logger.info(f"  ✅ Search 成功! 找到商品数量: {len(items)} 条")
            
            cur.execute(f"""
                INSERT INTO procurement_commodity_{plat}_search (procurement_id, brand_id, keyword, raw_data) 
                VALUES (%s, %s, %s, %s)
            """, (p_id, b_id, kw, Json(s_res)))

            # 更新为中间状态
            cur.execute("""
                INSERT INTO procurement_commodity_result (brand_id, procurement_id, status, server_ip, item_name) 
                VALUES (%s, %s, 'ai_processing', %s, %s)
                ON CONFLICT (brand_id, server_ip) DO UPDATE SET status = 'ai_processing', item_name = EXCLUDED.item_name;
            """, (b_id, p_id, s_ip, i_name))
            conn.commit()
            
            # 交棒给 AI：推送到初筛队列
            r_client.lpush("ai_filter_queue", json.dumps(task))
            logger.info(f"🎯 [交棒] 搜索完毕，已通知 AI 进行初筛。")

        else:
            logger.error(f"  ❌ Search API 彻底失败! 已重试 {max_retries} 次。")
            cur.execute("""
                INSERT INTO procurement_commodity_result (brand_id, procurement_id, status, server_ip, item_name, selection_reason) 
                VALUES (%s, %s, 'failed', %s, %s, %s)
                ON CONFLICT (brand_id, server_ip) DO UPDATE SET status = 'failed', selection_reason = EXCLUDED.selection_reason;
            """, (b_id, p_id, s_ip, i_name, f"外部商品接口抓取失败，已自动重试 {max_retries} 次仍无数据。"))
            conn.commit()

    except Exception as e:
        logger.error(f"❌ Worker Search阶段异常:", exc_info=True)
    finally:
        cur.close()
        conn.close()

def process_detail(task, r_client):
    """【第三棒】专属抓取详情 (加入 5 次重试机制)"""
    b_id = task.get('brand_id')
    p_id = task.get('procurement_id')
    plat = task.get('platform', 'taobao')
    top_5 = task.get('top_5_candidates', [])
    
    # 根据平台动态选择 Detail 接口
    if plat == 'jd':
        detail_api = 'item_get_pro'
    else:
        detail_api = 'item_get'
        
    logger.info(f"🚀 [阶段3: 详情抓取] BrandID: {b_id} | 准备抓取 {len(top_5)} 家详情数据...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    try:
        for i, c in enumerate(top_5, 1):
            num_iid = c.get('sku')
            if not num_iid: continue
            
            detail_url = f"https://api-gw.onebound.cn/{plat}/{detail_api}/"
            logger.info(f"  🔍 [{i}/{len(top_5)}] 正在调用 API: {plat}/{detail_api} | num_iid: {num_iid}")
            
            # ==========================================
            # 🔥 核心修复：为 Detail API 增加 5 次重试机制
            # ==========================================
            max_retries = 5
            success = False
            
            for attempt in range(1, max_retries + 1):
                try:
                    if attempt > 1: 
                        logger.info(f"    🔄 正在进行第 {attempt}/{max_retries} 次详情重试 (ID: {num_iid})...")
                        
                    d_res = requests.get(detail_url, params={"key": API_KEY, "secret": API_SECRET, "num_iid": num_iid}, timeout=15).json()
                    
                    if d_res.get("error_code") == "0000":
                        cur.execute(f"""
                            INSERT INTO procurement_commodity_{plat}_detail (procurement_id, brand_id, num_iid, raw_data) 
                            VALUES (%s, %s, %s, %s)
                        """, (p_id, b_id, str(num_iid), Json(d_res)))
                        logger.info(f"    ✅ Detail 抓取成功入库！")
                        success = True
                        break  # 成功抓取，跳出重试循环
                    else:
                        error_reason = d_res.get('reason', d_res)
                        logger.warning(f"    ⚠️ 第 {attempt} 次 Detail API 失败: {error_reason}")
                        
                except Exception as e:
                    logger.warning(f"    ⚠️ 第 {attempt} 次 Detail 网络异常: {e}")
                
                # 如果没成功且还有重试次数，休眠 3 秒后再试，防止被接口封控
                if attempt < max_retries: 
                    time.sleep(3)
            
            if not success:
                logger.error(f"    ❌ ID: {num_iid} 详情抓取彻底失败，已用尽 {max_retries} 次机会。")
                
        conn.commit()
        # 抓完详情，把带参数的任务包丢进最后一关：AI 终审队列
        r_client.lpush("ai_final_queue", json.dumps(task))
        logger.info(f"🎯 [交棒] Top {len(top_5)} 详情抓取流程结束，已通知 AI 进行终选。")
        
    except Exception as e:
        logger.error(f"❌ Worker Detail阶段异常: {e}", exc_info=True)
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    try:
        r = redis.Redis(**REDIS_CONFIG)
        r.ping()
        logger.info("✅ 成功连接至云端 Redis。")
        logger.info("📡 API Worker 启动，双引擎挂起，同时监听 [crawler_task_queue] 和 [crawler_detail_queue]...")
    except Exception as e:
        logger.critical(f"❌ 无法连接到 Redis: {e}")
        exit(1)

    while True:
        try:
            task_data = r.blpop(["crawler_task_queue", "crawler_detail_queue"], timeout=0)
            if task_data:
                queue_name = task_data[0]
                payload = json.loads(task_data[1])
                logger.info("-" * 60)
                if queue_name == "crawler_task_queue":
                    logger.info(f"🔔 收到 [全网搜索] 任务: BrandID {payload.get('brand_id')}")
                    process_search(payload, r)
                elif queue_name == "crawler_detail_queue":
                    logger.info(f"🔔 收到 [抓取详情] 任务: BrandID {payload.get('brand_id')}")
                    process_detail(payload, r)
        except Exception as e:
            logger.error(f"❌ 轮询队列异常: {e}")
            time.sleep(5)