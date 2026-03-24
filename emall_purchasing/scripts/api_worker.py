# coding:utf-8
import redis
import json
import psycopg2
import requests
from psycopg2.extras import Json

DB_CONFIG = {'host': '121.43.77.214', 'port': 5432, 'dbname': 'austinchen587_db', 'user': 'austinchen587', 'password': 'austinchen587'}
REDIS_CONFIG = {'host': '121.43.77.214', 'port': 6379, 'password': 'austinchen587', 'decode_responses': True}
API_KEY = "t3970966868"
API_SECRET = "6868cdc9"

# 👉 修复：把 Redis client (r_client) 传进函数，方便后面发通知
def process_task(task, r_client):
    b_id = task['brand_id']
    p_id = task['procurement_id']
    s_ip = task.get('server_ip', 'unknown') # 👉 获取分派任务的服务器 IP
    i_name = task.get('item_name', '未知商品') # 👉 获取商品名称
    kw = task['key_word']
    platform_raw = task['platform'].lower()
    
    plat = 'jd' if 'jd' in platform_raw else ('1688' if '1688' in platform_raw else 'taobao')
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    try:
        # 1. 抓取 Search
        search_url = f"https://api-gw.onebound.cn/{plat}/item_search/"
        s_res = requests.get(search_url, params={"key": API_KEY, "secret": API_SECRET, "q": kw}).json()
        
        if s_res.get("error_code") == "0000":
            cur.execute(f"""
                INSERT INTO procurement_commodity_{plat}_search (procurement_id, brand_id, keyword, raw_data) 
                VALUES (%s, %s, %s, %s)
            """, (p_id, b_id, kw, Json(s_res)))

            # 2. 抓取 Detail
            items = s_res.get("items", {}).get("item", [])
            if items:
                num_iid = items[0].get("num_iid")
                detail_url = f"https://api-gw.onebound.cn/{plat}/item_get/"
                d_res = requests.get(detail_url, params={"key": API_KEY, "secret": API_SECRET, "num_iid": num_iid}).json()
                
                if d_res.get("error_code") == "0000":
                    cur.execute(f"""
                        INSERT INTO procurement_commodity_{plat}_detail (procurement_id, brand_id, num_iid, raw_data) 
                        VALUES (%s, %s, %s, %s)
                    """, (p_id, b_id, num_iid, Json(d_res)))

            # =========================================================
            # 🔥 3. 核心修复：更新状态并交棒给 AI！
            # =========================================================
            # 状态必须是 'ai_processing'，这样 progress_services.py 就不会去拉取它
            cur.execute("""
                INSERT INTO procurement_commodity_result (brand_id, procurement_id, status, server_ip, item_name) 
                VALUES (%s, %s, 'ai_processing', %s, %s)
                ON CONFLICT (brand_id) 
                DO UPDATE SET status = 'ai_processing', server_ip = EXCLUDED.server_ip, item_name = EXCLUDED.item_name;
            """, (b_id, p_id, s_ip, i_name))
            
            conn.commit()
            print(f"✅ 爬虫抓取完毕，数据已入库: BrandID {b_id} | ServerIP {s_ip}")
            
            # 4. 🚀 向 AI 大脑发送开工信号！
            ai_signal = {
                "brand_id": b_id,
                "server_ip": s_ip
            }
            r_client.lpush("ai_selection_queue", json.dumps(ai_signal))
            print(f"📡 已通知 AI 节点接手工作: {ai_signal}")

    except Exception as e:
        print(f"❌ 处理失败: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    r = redis.Redis(**REDIS_CONFIG)
    print("📡 API Worker 已启动，正在监听任务队列...")
    while True:
        task_data = r.brpop("crawler_task_queue", timeout=30)
        if task_data:
            # 👉 传入 r 实例
            process_task(json.loads(task_data[1]), r)