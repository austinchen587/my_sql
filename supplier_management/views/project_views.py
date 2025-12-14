# supplier_management/views/project_views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from emall_purchasing.models import ProcurementPurchasing
from emall.models import ProcurementEmall
from .base_views import create_error_response

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
            'bidding_status': purchasing.bidding_status,  # code，如 'not_started'
            'bidding_status_display': purchasing.get_bidding_status_display(),  # 中文，如 '未开始'
        })
    
    return Response(projects)

@api_view(['GET'])
def project_list_success(request):
    """获取竞标成功的项目列表 - 只返回前端需要的字段"""
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

# supplier_management/views/project_views.py - 更新 get_project_suppliers 函数
@api_view(['GET'])
def get_project_suppliers(request):
    """获取项目供应商 - 包含审计字段"""
    project_id = request.GET.get('project_id')
    
    print(f"DEBUG: Received project_id = {project_id}")
    
    if not project_id:
        # 返回所有已选中项目的列表
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
            print(f"DEBUG: Error fetching project list: {e}")
            return create_error_response('获取项目列表失败', 500)
    
    try:
        # 直接通过 ProcurementPurchasing 查询
        print(f"DEBUG: Looking for ProcurementPurchasing with procurement_id={project_id}")
        purchasing = ProcurementPurchasing.objects.get(procurement_id=project_id, is_selected=True)
        print(f"DEBUG: Found purchasing info for project_id: {project_id}")
        
        # 获取供应商信息
        suppliers_info = []
        total_selected_quote = 0
        
        # 遍历 ProcurementSupplier 关系表获取供应商数据
        procurement_suppliers = purchasing.procurementsupplier_set.all()
        print(f"DEBUG: Found {procurement_suppliers.count()} supplier relations")
        
        for procurement_supplier in procurement_suppliers:
            supplier = procurement_supplier.supplier
            total_quote = procurement_supplier.get_total_quote()
            
            if procurement_supplier.is_selected:
                total_selected_quote += float(total_quote) if total_quote else 0
            
            # 获取商品信息，包含审计字段
            commodities_data = []
            try:
                from emall_purchasing.models import SupplierCommodity
                for commodity in supplier.commodities.all():
                    commodities_data.append({
                        'id': commodity.id,
                        'name': commodity.name,
                        'specification': commodity.specification or '',
                        'price': float(commodity.price) if commodity.price else 0,
                        'quantity': commodity.quantity or 0,
                        'product_url': commodity.product_url or '',
                        # 新增：支付和物流字段
                        'payment_amount': float(commodity.payment_amount) if commodity.payment_amount is not None else None,
                        'tracking_number': commodity.tracking_number or '',
                        # 添加商品审计字段
                        'purchaser_created_by': commodity.purchaser_created_by,
                        'purchaser_created_at': commodity.purchaser_created_at.isoformat() if commodity.purchaser_created_at else None
                    })
            except Exception as e:
                print(f"DEBUG: Error fetching commodities for supplier {supplier.id}: {e}")
                commodities_data = []
            
            supplier_data = {
                'id': supplier.id,
                'name': supplier.name,
                'source': supplier.source,
                'contact': supplier.contact,
                'store_name': supplier.store_name,
                'is_selected': procurement_supplier.is_selected,
                'total_quote': float(total_quote) if total_quote else 0,
                'commodities': commodities_data,
                # 添加供应商审计字段
                'purchaser_created_by': supplier.purchaser_created_by,
                'purchaser_created_at': supplier.purchaser_created_at.isoformat() if supplier.purchaser_created_at else None,
                'purchaser_updated_by': supplier.purchaser_updated_by,
                'purchaser_updated_at': supplier.purchaser_updated_at.isoformat() if supplier.purchaser_updated_at else None,
                # 添加供应商关系审计字段
                'procurement_supplier_created_by': procurement_supplier.purchaser_created_by,
                'procurement_supplier_created_at': procurement_supplier.purchaser_created_at.isoformat() if procurement_supplier.purchaser_created_at else None,
                'procurement_supplier_updated_by': procurement_supplier.purchaser_updated_by,
                'procurement_supplier_updated_at': procurement_supplier.purchaser_updated_at.isoformat() if procurement_supplier.purchaser_updated_at else None
            }
            
            suppliers_info.append(supplier_data)
        
        # 计算利润
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
        
        print(f"DEBUG: Returning data for {len(suppliers_info)} suppliers")
        return Response(response_data)
        
    except ProcurementPurchasing.DoesNotExist:
        print(f"DEBUG: ProcurementPurchasing with procurement_id {project_id} does not exist")
        return create_error_response('项目不存在或未被选中', 404)
    except Exception as e:
        print(f"DEBUG: Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_error_response(f'服务器内部错误: {str(e)}', 500)
