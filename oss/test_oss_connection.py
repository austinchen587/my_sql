# test_oss_connection.py
import requests
import json

def test_oss_apis():
    base_url = "http://localhost:8000/api/oss/"
    
    print("=== 测试OSS连接 ===")
    try:
        response = requests.get(base_url + "test-connection/")
        result = response.json()
        print(f"状态码: {response.status_code}")
        print(f"响应结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if result.get('success'):
            print("✅ OSS连接测试成功！")
        else:
            print("❌ OSS连接测试失败！")
            print(f"错误信息: {result.get('error')}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到Django服务器，请确保服务器正在运行")
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    test_oss_apis()
