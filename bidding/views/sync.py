import threading
from django.core.management import call_command
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny

@api_view(['POST'])
@authentication_classes([]) 
@permission_classes([AllowAny])
def sync_province_data(request):
    """
    触发后台同步任务的接口
    URL: /api/bidding/sync/
    Body: { "province": "JX" }
    """
    province = request.data.get('province')
    
    if not province:
        return Response({'success': False, 'message': '缺少 province 参数'}, status=400)

    # 定义后台任务函数
    def run_sync_command():
        try:
            print(f"🚀 [后台任务] 开始同步省份数据: {province}...")
            # 调用 management command 执行实际爬虫逻辑
            call_command('sync_bidding', province=province)
            print(f"✅ [后台任务] 省份 {province} 同步完成")
        except Exception as e:
            print(f"❌ [后台任务] 同步失败: {e}")

    # 启动守护线程执行
    thread = threading.Thread(target=run_sync_command, daemon=True)
    thread.start()
    
    return Response({
        'success': True,
        'message': f'已成功触发 {province} 地区的数据同步任务'
    })