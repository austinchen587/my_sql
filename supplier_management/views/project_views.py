# supplier_management/views/project_views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from emall_purchasing.models import ProcurementPurchasing, ProcurementSupplier, Supplier, SupplierCommodity

# [核心修复] ProcurementEmall 在 emall 应用
from emall.models import ProcurementEmall

# [核心修复] ProcurementCommodityBrand 和 Result 通常都在 bidding 应用
from bidding.models import ProcurementCommodityResult, ProcurementCommodityBrand

from .base_views import create_error_response
import json
import logging
import re

logger = logging.getLogger(__name__)

@api_view(['GET'])
def project_list(request):
    """获取项目列表 - 只返回前端需要的字段"""
    time_filter = request.GET.get('time_filter', 'today')
    
    queryset = ProcurementPurchasing.objects.filter(is_selected=True)
    
    # 时间过滤逻辑
    now = timezone.now()
    if time_filter == 'today':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        queryset = queryset.filter(selected_at__gte=start_date)
    elif time_filter == 'yesterday':
        yesterday = now - timedelta(days=1)
        start_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        queryset = queryset.filter(selected_at__range=(start_date, end_date))
    elif time_filter == 'this_week':
        start_date = now - timedelta(days=now.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        queryset = queryset.filter(selected_at__gte=start_date)
    elif time_filter == 'this_month':
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        queryset = queryset.filter(selected_at__gte=start_date)
    
    projects = []
    for purchasing in queryset.order_by('-selected_at'):
        projects.append({
            'id': purchasing.procurement.id,
            'project_title': purchasing.procurement.project_title,
            'project_name': purchasing.procurement.project_name,
            'total_price_control': purchasing.procurement.total_price_control,
            'selected_at': purchasing.selected_at,
            'supplier_count': purchasing.procurementsupplier_set.count(),
            'project_owner': purchasing.project_owner,
            'bidding_status': purchasing.bidding_status,
            'bidding_status_display': purchasing.get_bidding_status_display(),
            'region': purchasing.procurement.region,
        })
    
    return Response(projects)

@api_view(['GET'])
def project_list_success(request):
    """获取竞标成功的项目列表"""
    queryset = ProcurementPurchasing.objects.filter(is_selected=True, bidding_status='successful')
    projects = []
    for purchasing in queryset.order_by('-selected_at'):
        projects.append({
            'id': purchasing.procurement.id,
            'project_title': purchasing.procurement.project_title,
            'project_name': purchasing.procurement.project_name,
            'total_price_control': purchasing.procurement.total_price_control,
            'selected_at': purchasing.selected_at,
            'supplier_count': purchasing.procurementsupplier_set.count(),
            'project_owner': purchasing.project_owner,
            'bidding_status': purchasing.bidding_status,
            'bidding_status_display': purchasing.get_bidding_status_display(),
        })
    return Response(projects)

@api_view(['GET'])
def get_project_suppliers(request):
    """获取项目供应商 - 修复数量、价格和商品丢失问题"""
    project_id = request.GET.get('project_id')
    
    if not project_id:
        try:
            selected_projects = ProcurementPurchasing.objects.filter(is_selected=True)
            project_list = []
            for purchasing in selected_projects:
                project_list.append({
                    'id': purchasing.procurement.id,
                    'project_title': purchasing.procurement.project_title,
                    'total_budget': float(purchasing.get_total_budget()) if purchasing.get_total_budget() else 0,
                    'supplier_count': purchasing.procurementsupplier_set.count(),
                    'hint': '请在URL中添加 ?project_id=项目ID 来获取具体供应商信息'
                })
            return Response({
                'message': '请选择具体项目查看供应商详情',
                'available_projects': project_list,
                'usage': '使用 /api/supplier/project-suppliers/?project_id=项目ID 获取具体供应商信息'
            })
        except Exception as e:
            return create_error_response('获取项目列表失败', 500)
    
    try:
        purchasing = ProcurementPurchasing.objects.get(procurement_id=str(project_id), is_selected=True)
        current_user = request.user.username if request.user.is_authenticated else '系统AI'

        # ==========================================
        # [核心修复]：自动同步 AI 推荐结果
        # ==========================================
        try:
            ai_results = ProcurementCommodityResult.objects.filter(procurement_id=str(project_id))
            
            # 预加载需求表 (用于获取数量)
            brand_map = {}
            brands = ProcurementCommodityBrand.objects.filter(procurement_id=str(project_id))
            for b in brands:
                brand_map[b.id] = b

            for res in ai_results:
                try:
                    if not res.selected_suppliers:
                        continue
                    
                    # 1. 解析 JSON
                    candidates = []
                    raw_str = res.selected_suppliers
                    try:
                        candidates = json.loads(raw_str)
                    except:
                        try:
                            clean_str = raw_str.replace('""', '"')
                            if clean_str.startswith('"') and clean_str.endswith('"'):
                                clean_str = clean_str[1:-1]
                            candidates = json.loads(clean_str)
                        except:
                            continue

                    # 2. 获取数量 (从 Brand 表提取)
                    req_quantity = 1
                    if res.brand_id and res.brand_id in brand_map:
                        brand_obj = brand_map[res.brand_id]
                        if brand_obj.quantity:
                            # 提取数字 (如 "10个" -> 10)
                            qty_str = str(brand_obj.quantity)
                            match = re.search(r'(\d+)', qty_str)
                            if match:
                                req_quantity = int(match.group(1))

                    # 3. 遍历推荐项
                    for item in candidates:
                        # [策略] 只自动导入 Rank 1 的商品
                        rank = item.get('rank', 99)
                        if rank != 1: 
                            continue 

                        shop_name = item.get('shop', '未知店铺')
                        platform = item.get('platform', '未知平台')
                        
                        # 解析价格
                        try:
                            price_val = float(item.get('price', 0))
                        except:
                            price_val = 0

                        # --- A. 确保供应商存在 ---
                        supplier, _ = Supplier.objects.get_or_create(
                            name=shop_name,
                            defaults={
                                'source': f"AI推荐-{platform}",
                                'store_name': shop_name,
                                'contact': 'AI自动采集',
                                'purchaser_created_by': current_user,
                                'purchaser_updated_by': current_user
                            }
                        )

                        # --- B. 建立项目关联 ---
                        ProcurementSupplier.objects.get_or_create(
                            procurement=purchasing,
                            supplier=supplier,
                            defaults={
                                'is_selected': False,
                                'purchaser_created_by': current_user,
                                'purchaser_updated_by': current_user
                            }
                        )

                        # --- C. 确保商品存在 ---
                        item_name = res.item_name or '未命名商品'
                        
                        comm_qs = SupplierCommodity.objects.filter(
                            supplier=supplier,
                            name=item_name
                        )
                        
                        if not comm_qs.exists():
                            SupplierCommodity.objects.create(
                                supplier=supplier,
                                name=item_name,
                                specification=res.specifications or '',
                                price=price_val,       
                                quantity=req_quantity, 
                                product_url=item.get('detail_url', ''),
                                payment_amount=0,
                                tracking_number='',
                                purchaser_created_by=current_user
                            )
                        else:
                            # 如果已存在，更新价格和数量
                            comm = comm_qs.first()
                            if comm.price != price_val or comm.quantity != req_quantity:
                                comm.price = price_val
                                comm.quantity = req_quantity
                                comm.save()

                except Exception as inner_e:
                    logger.error(f"处理单条AI结果失败 (ID: {res.id}): {inner_e}")
                    continue

        except Exception as e:
            logger.error(f"AI Sync Error: {e}")

        # ==========================================
        # 返回数据
        # ==========================================
        
        suppliers_info = []
        total_selected_quote = 0
        
        procurement_suppliers = purchasing.procurementsupplier_set.all()
        
        for procurement_supplier in procurement_suppliers:
            supplier = procurement_supplier.supplier
            total_quote = procurement_supplier.get_total_quote()
            
            if procurement_supplier.is_selected:
                total_selected_quote += float(total_quote) if total_quote else 0
            
            # 获取商品信息
            commodities_data = []
            for commodity in supplier.commodities.all():
                commodities_data.append({
                    'id': commodity.id,
                    'name': commodity.name,
                    'specification': commodity.specification or '',
                    'price': float(commodity.price) if commodity.price else 0,
                    'quantity': commodity.quantity or 0,
                    'product_url': commodity.product_url or '',
                    'payment_amount': float(commodity.payment_amount) if commodity.payment_amount is not None else None,
                    'tracking_number': commodity.tracking_number or '',
                    'purchaser_created_by': commodity.purchaser_created_by,
                    'purchaser_created_at': commodity.purchaser_created_at.isoformat() if commodity.purchaser_created_at else None
                })
            
            supplier_data = {
                'id': supplier.id,
                'name': supplier.name,
                'source': supplier.source,
                'contact': supplier.contact,
                'store_name': supplier.store_name,
                'is_selected': procurement_supplier.is_selected,
                'total_quote': float(total_quote) if total_quote else 0,
                'commodities': commodities_data,
                'purchaser_created_by': supplier.purchaser_created_by,
                'purchaser_created_at': supplier.purchaser_created_at.isoformat() if supplier.purchaser_created_at else None,
                'purchaser_updated_by': supplier.purchaser_updated_by,
                'purchaser_updated_at': supplier.purchaser_updated_at.isoformat() if supplier.purchaser_updated_at else None,
                'procurement_supplier_created_by': procurement_supplier.purchaser_created_by,
                'procurement_supplier_created_at': procurement_supplier.purchaser_created_at.isoformat() if procurement_supplier.purchaser_created_at else None,
                'procurement_supplier_updated_by': procurement_supplier.purchaser_updated_by,
                'procurement_supplier_updated_at': procurement_supplier.purchaser_updated_at.isoformat() if procurement_supplier.purchaser_updated_at else None
            }
            
            suppliers_info.append(supplier_data)
        
        budget = purchasing.get_total_budget()
        budget_float = float(budget) if budget else 0
        total_profit = budget_float - total_selected_quote if budget_float > total_selected_quote else 0
        
        response_data = {
            'project_info': {
                'id': purchasing.procurement.id,
                'project_title': purchasing.procurement.project_title,
                'total_budget': budget_float,
                'total_selected_quote': total_selected_quote,
                'total_profit': total_profit
            },
            'suppliers': suppliers_info
        }
        
        return Response(response_data)
        
    except ProcurementPurchasing.DoesNotExist:
        return create_error_response('项目不存在或未被选中', 404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return create_error_response(f'服务器内部错误: {str(e)}', 500)