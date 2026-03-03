import threading
import logging 
from django.core.management import call_command
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from ..models import ProcurementCommodityResult, ProcurementCommodityBrand

logger = logging.getLogger(__name__)

@api_view(['POST'])
@authentication_classes([]) 
@permission_classes([AllowAny])
def sync_province_data(request):
    """
    触发后台同步任务的接口
    URL: /api/bidding/sync/
    """
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
    """
    单商品重试 & 修改关键词接口
    URL: /api/bidding/item/retry/
    """
    brand_id = request.data.get('brand_id')
    new_keyword = request.data.get('new_keyword')
    new_platform = request.data.get('new_platform') # 接收前端传来的新平台
    
    logger.info(f"📥 [人工派单] 收到前端重新寻源指令 | BrandID={brand_id} | 新关键词='{new_keyword}' | 新平台='{new_platform}'")
    
    if not brand_id:
        logger.warning("❌ [人工派单] 失败：缺少商品ID (brand_id)")
        return Response({'success': False, 'message': '缺少商品ID (brand_id)'}, status=400)

    try:
        # 1. 动态构造更新字段，同时写入 keyword 和 search_platform
        update_fields = {}
        if new_keyword:
            update_fields['key_word'] = new_keyword
        if new_platform:
            update_fields['search_platform'] = new_platform
            
        if update_fields:
            ProcurementCommodityBrand.objects.filter(id=brand_id).update(**update_fields)
            logger.info(f"   ✏️ [数据库] 已更新 Brand 表字段: {update_fields}")

        # 2. 将对应 brand_id 的结果状态改为 retry，并重置原因
        updated_count = ProcurementCommodityResult.objects.filter(brand_id=brand_id).update(
            status='retry',
            selection_reason='AI 正在全网寻源中，请稍后刷新...'
        )
        
        # 3. 如果结果表里连记录都没有，创建一条占位符
        if updated_count == 0:
            ProcurementCommodityResult.objects.create(
                brand_id=brand_id,
                item_name="前端触发手动重试",
                selection_reason="AI 正在全网寻源中，请稍后刷新...",
                status='retry'
            )
            logger.info(f"   ➕ [数据库] Result 表中无历史记录，已创建全新的 retry 占位符")
        else:
            logger.info(f"   🔄 [数据库] 已将 Result 表中的历史状态重置为 'retry'")

        logger.info(f"✅ [人工派单] 成功！商品 (BrandID={brand_id}) 已加入 AI 爬虫队列...")

        return Response({
            'success': True, 
            'message': '✅ 已加入寻源队列，预计 1-3 分钟后出结果'
        })
        
    except Exception as e:
        logger.error(f"❌ [人工派单] 数据库操作失败: {str(e)}")
        return Response({'success': False, 'message': f'操作失败: {str(e)}'}, status=500)