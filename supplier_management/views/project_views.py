# supplier_management/views/project_views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from django.db.models import Q
from emall_purchasing.models import ProcurementPurchasing, ProcurementSupplier, Supplier, SupplierCommodity
from emall.models import ProcurementEmall
from bidding.models import ProcurementCommodityResult, ProcurementCommodityBrand
from .base_views import create_error_response, create_success_response
import json
import logging
import re  # 必须引入正则

logger = logging.getLogger(__name__)

# ==============================================================================
#  核心辅助函数：AI 自动导入 + 强制数据修正
# ==============================================================================

def extract_quantity(text):
    """从文本中提取最可能的数量"""
    if not text: return 1
    s = str(text)
    # 1. 尝试直接转换
    try:
        return int(float(s))
    except:
        pass
    
    # 2. 优先匹配 "数字+单位" (如 6800箱, 500个)
    match = re.search(r'(\d+)\s*(?:箱|件|瓶|个|只|双|台|套|包|捆)', s)
    if match:
        return int(match.group(1))
    
    # 3. 兜底：提取第一个纯数字
    match = re.search(r'(\d+)', s)
    if match:
        return int(match.group(1))
        
    return 1

def auto_import_from_ai(purchasing):
    """AI 自动导入 + 数据自愈逻辑"""
    try:
        procurement_id = purchasing.procurement.id
        print(f"\n\033[93m[AutoImport] 开始处理项目 (ID: {procurement_id})...\033[0m")

        # 1. 获取需求清单 (Brand) - 建立 ID 映射
        brands = ProcurementCommodityBrand.objects.filter(procurement_id=procurement_id)
        requirement_map = {} # Key: brand_id, Value: quantity
        name_fallback_map = {} # Key: name, Value: quantity
        
        for b in brands:
            qty = extract_quantity(b.quantity)
            requirement_map[b.id] = qty
            name_fallback_map[b.item_name] = qty

        # 2. 获取 AI 结果
        ai_results = ProcurementCommodityResult.objects.filter(procurement_id=procurement_id)
        if not ai_results.exists() and brands.exists():
            brand_ids = list(brands.values_list('id', flat=True))
            ai_results = ProcurementCommodityResult.objects.filter(brand_id__in=brand_ids)

        if not ai_results.exists():
            return False

        imported_count = 0
        
        with transaction.atomic():
            for res in ai_results:
                if not res.selected_suppliers:
                    continue
                
                # 确定该商品的正确数量 (优先用 brand_id)
                true_quantity = 1
                if res.brand_id and res.brand_id in requirement_map:
                    true_quantity = requirement_map[res.brand_id]
                elif res.item_name in name_fallback_map:
                    true_quantity = name_fallback_map[res.item_name]
                
                # 解析 JSON
                try:
                    clean_str = res.selected_suppliers.replace('""', '"')
                    if clean_str.startswith('"') and clean_str.endswith('"'):
                        clean_str = clean_str[1:-1]
                    suppliers_data = json.loads(clean_str)
                except:
                    continue

                if not isinstance(suppliers_data, list):
                    continue

                for item in suppliers_data:
                    shop_name = item.get('shop', '未知店铺')
                    if not shop_name: continue
                    
                    try:
                        price = float(item.get('price', 0))
                    except:
                        price = 0
                    url = item.get('detail_url', '') or item.get('link', '')

                    # 确保供应商存在
                    supplier, _ = Supplier.objects.get_or_create(
                        name=shop_name,
                        defaults={'source': 'AI推荐', 'contact': '系统自动采集', 'store_name': shop_name}
                    )

                    # 关联供应商
                    ProcurementSupplier.objects.get_or_create(
                        procurement=purchasing,
                        supplier=supplier,
                        defaults={'is_selected': False, 'purchaser_created_by': 'System(AI)'}
                    )

                    # --- 商品处理逻辑 ---
                    # 注意：由于 SupplierCommodity 没有 brand_id 字段，只能按名字匹配
                    # 如果同一个供应商对两个同名不同规格的商品都有报价，这里可能会混淆，这是当前数据模型的限制
                    comm_qs = SupplierCommodity.objects.filter(supplier=supplier, name=res.item_name)
                    
                    if comm_qs.exists():
                        # [自愈]：如果商品已存在且数量为1，尝试修正为需求数量
                        comm = comm_qs.first()
                        if comm.quantity != true_quantity and true_quantity > 1:
                            # 只有当现有数量看起来像是默认值(1)时才覆盖，防止覆盖人工修改
                            if comm.quantity == 1: 
                                print(f"\033[93m[Fix] 修正数量 {comm.name}: {comm.quantity} -> {true_quantity}\033[0m")
                                comm.quantity = true_quantity
                                comm.save()
                    else:
                        # 创建新商品
                        SupplierCommodity.objects.create(
                            supplier=supplier,
                            name=res.item_name,
                            specification=res.specifications or '详见链接',
                            price=price,
                            quantity=true_quantity, # 使用正确数量
                            product_url=url
                        )
                        imported_count += 1
        
        return True

    except Exception as e:
        logger.error(f"导入失败: {e}")
        return False

# ==============================================================================
#  视图函数
# ==============================================================================

@api_view(['GET'])
def project_list(request):
    """获取进行中的项目列表"""
    time_filter = request.GET.get('time_filter', 'today')
    queryset = ProcurementPurchasing.objects.filter(is_selected=True).select_related('procurement')
    
    now = timezone.now()
    if time_filter == 'today':
        start = now.replace(hour=0, minute=0, second=0)
        queryset = queryset.filter(selected_at__gte=start)
    elif time_filter == 'yesterday':
        yesterday = now - timedelta(days=1)
        start_date = yesterday.replace(hour=0, minute=0, second=0)
        end_date = yesterday.replace(hour=23, minute=59, second=59)
        queryset = queryset.filter(selected_at__range=(start_date, end_date))
    elif time_filter == 'this_week':
        start_date = now - timedelta(days=now.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0)
        queryset = queryset.filter(selected_at__gte=start_date)
    elif time_filter == 'this_month':
        start_date = now.replace(day=1, hour=0, minute=0, second=0)
        queryset = queryset.filter(selected_at__gte=start_date)
    
    data = []
    for item in queryset:
        supplier_count = ProcurementSupplier.objects.filter(procurement=item).count()
        data.append({
            'id': item.procurement.id,
            'project_name': item.procurement.project_title,
            'total_price_control': item.procurement.total_price_control,
            'selected_at': item.selected_at,
            'project_owner': item.project_owner,
            'supplier_count': supplier_count,
            'bidding_status': item.bidding_status,
            'bidding_status_display': item.get_bidding_status_display()
        })
    return Response(data)

@api_view(['GET'])
def project_list_success(request):
    """获取竞标成功的项目列表"""
    queryset = ProcurementPurchasing.objects.filter(
        is_selected=True,
        bidding_status='successful'
    ).select_related('procurement').order_by('-selected_at')
    
    data = []
    for item in queryset:
        supplier_count = ProcurementSupplier.objects.filter(procurement=item).count()
        data.append({
            'id': item.procurement.id,
            'project_name': item.procurement.project_title,
            'total_price_control': item.procurement.total_price_control,
            'selected_at': item.selected_at,
            'project_owner': item.project_owner,
            'supplier_count': supplier_count,
            'bidding_status': item.bidding_status,
            'bidding_status_display': item.get_bidding_status_display()
        })
    return Response(data)

@api_view(['GET'])
def get_project_suppliers(request):
    """
    获取项目供应商数据
    """
    project_id = request.GET.get('project_id')
    if not project_id: return create_error_response('缺少 project_id')
        
    try:
        try:
            purchasing = ProcurementPurchasing.objects.get(procurement_id=project_id, is_selected=True)
        except:
            return create_error_response('项目未找到', 404)

        # 1. 触发一次自动导入/修正
        auto_import_from_ai(purchasing)

        # 2. 获取所有供应商数据
        suppliers_queryset = ProcurementSupplier.objects.filter(procurement=purchasing)
        suppliers_info = []
        total_selected_quote = 0
        
        for ps in suppliers_queryset:
            supplier = ps.supplier
            # 查找该供应商在这个项目里的所有商品
            commodities = SupplierCommodity.objects.filter(supplier=supplier)
            
            comm_data = []
            s_total = 0
            for c in commodities:
                qty = int(c.quantity or 0)
                price = float(c.price or 0)
                row_total = qty * price
                s_total += row_total
                
                comm_data.append({
                    'id': c.id,
                    'name': c.name,
                    'specification': c.specification,
                    'price': price,
                    'quantity': qty,
                    'total_price': row_total,
                    'product_url': c.product_url,
                    # 安全字段
                    'shipping_cost': getattr(c, 'shipping_cost', 0),
                    'is_included_shipping': getattr(c, 'is_included_shipping', False),
                    'delivery_days': getattr(c, 'delivery_days', None),
                    'payment_amount': getattr(c, 'payment_amount', None),
                    'tracking_number': getattr(c, 'tracking_number', None)
                })
            
            if ps.is_selected:
                total_selected_quote += s_total

            suppliers_info.append({
                'id': supplier.id,
                'name': supplier.name,
                'source': supplier.source,
                'contact': supplier.contact,
                'store_name': supplier.store_name,
                'is_selected': ps.is_selected,
                'status': getattr(ps, 'status', 'pending'),
                'total_price': s_total,
                'commodities': comm_data,
                'purchaser_created_at': ps.purchaser_created_at.isoformat() if ps.purchaser_created_at else None,
            })

        # 3. [关键修复] 获取需求清单，使用 Brand ID 作为 Key
        # 这样即使有同名商品，前端也能区分开
        requirements = {}
        brands = ProcurementCommodityBrand.objects.filter(procurement_id=purchasing.procurement.id)
        for b in brands:
            qty_num = extract_quantity(b.quantity)
            # 使用 b.id (Brand ID) 作为唯一键
            requirements[str(b.id)] = {
                'name': b.item_name,    # 名字作为属性传给前端
                'original_qty_str': b.quantity,
                'required_qty': qty_num,
                'unit': b.unit,
                'spec': b.specifications
            }

        # 构建响应
        budget = purchasing.get_total_budget() or 0
        budget_float = float(budget)
        
        # [补充计算利润逻辑]：预算 - 已采纳的供应商成本
        total_profit = budget_float - total_selected_quote if budget_float > total_selected_quote else 0

        response_data = {
            'project_info': {
                'id': purchasing.procurement.id,
                'project_title': purchasing.procurement.project_title,
                'total_budget': budget_float,
                'total_selected_quote': total_selected_quote,
                'total_profit': total_profit,  # [核心修复] 将计算好的利润返回给前端
            },
            'suppliers': suppliers_info,
            'requirements': requirements  
        }


        
        return Response(response_data)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return create_error_response(f'Error: {str(e)}', 500)