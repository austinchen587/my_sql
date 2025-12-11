# test_oss_upload_no_proxy.py
import requests
import os
import time

def test_oss_upload_no_proxy():
    print("=== 测试文件上传（绕过代理）===")
    
    # 设置不适用代理
    session = requests.Session()
    session.trust_env = False  # 不读取系统代理设置
    
    # 或者直接设置空代理
    proxies = {
        'http': None,
        'https': None
    }
    
    # 创建测试文件
    test_filename = f"test_upload_{int(time.time())}.txt"
    with open(test_filename, 'w', encoding='utf-8') as f:
        f.write(f'这是OSS上传测试文件内容，创建时间: {time.ctime()}')
    
    try:
        with open(test_filename, 'rb') as f:
            files = {'file': (test_filename, f)}
            
            # 使用session请求，绕过代理
            response = session.post(
                'http://localhost:8000/api/oss/upload-test/',
                files=files,
                proxies=proxies,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print("✅ 文件上传成功！")
                    print(f"   文件URL: {result.get('url')}")
                    print(f"   Object名称: {result.get('object_name')}")
                else:
                    print("❌ 上传失败:", result.get('error', '未知错误'))
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                print(f"   响应内容: {response.text}")
                
    except requests.exceptions.ProxyError as e:
        print("❌ 代理错误:", e)
        print("尝试使用更直接的方法...")
        test_direct_connection()
        
    except requests.exceptions.ConnectionError as e:
        print("❌ 连接错误:", e)
        print("请检查Django服务器是否正在运行")
        
    except requests.exceptions.Timeout as e:
        print("❌ 请求超时:", e)
        
    except Exception as e:
        print("❌ 测试过程中发生错误:", e)
        
    finally:
        # 清理测试文件
        if os.path.exists(test_filename):
            os.remove(test_filename)

def test_direct_connection():
    """测试直接连接"""
    print("\n=== 测试直接连接 ===")
    try:
        # 使用urllib3直接连接，避免代理
        import urllib3
        import json
        
        # 禁用SSL警告
        urllib3.disable_warnings()
        
        http = urllib3.PoolManager()
        
        # 测试连接
        response = http.request('GET', 'http://localhost:8000/api/oss/test-connection/')
        if response.status == 200:
            result = json.loads(response.data.decode('utf-8'))
            if result.get('success'):
                print("✅ 直接连接测试成功")
            else:
                print("❌ 直接连接测试失败")
        else:
            print(f"❌ HTTP状态码: {response.status}")
            
    except Exception as e:
        print("❌ 直接连接测试错误:", e)

if __name__ == "__main__":
    test_oss_upload_no_proxy()
