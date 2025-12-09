# supplier_management/views/supplier_views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from emall_purchasing.models import ProcurementPurchasing, ProcurementSupplier, Supplier, SupplierCommodity
from emall.models import ProcurementEmall
from .base_views import create_error_response, create_success_response

@api_view(['POST'])
def toggle_supplier_selection(request):
    """切换供应商选择状态 - 修复版本"""
    supplier_id = request.data.get('supplier_id')
    project_id = request.data.get('project_id')
    is_selected = request.data.get('is_selected')
    
    print(f"DEBUG: toggle_selection - project_id: {project_id}, supplier_id: {supplier_id}, is_selected: {is_selected}")
    
    try:
        # 直接通过 ProcurementPurchasing 查询，更可靠
        purchasing = ProcurementPurchasing.objects.get(procurement_id=project_id, is_selected=True)
        
        procurement_supplier = ProcurementSupplier.objects.get(
            procurement=purchasing, 
            supplier_id=supplier_id
        )
        
        # 确保 is_selected 是布尔值
        procurement_supplier.is_selected = bool(is_selected)
        procurement_supplier.save()
        
        print(f"DEBUG: Successfully toggled selection for supplier {supplier_id}")
        
        return create_success_response(f'供应商{"已选择" if is_selected else "已取消选择"}')
        
    except ProcurementPurchasing.DoesNotExist:
        print(f"DEBUG: ProcurementPurchasing not found for project_id: {project_id}")
        return create_error_response('项目不存在或未被选中', 404)
    except ProcurementSupplier.DoesNotExist:
        print(f"DEBUG: ProcurementSupplier not found for supplier_id: {supplier_id}")
        return create_error_response('供应商关系不存在', 404)
    except Exception as e:
        print(f"DEBUG: Unexpected error: {str(e)}")
        return create_error_response(f'服务器内部错误: {str(e)}', 500)

@api_view(['POST'])
def update_supplier(request):
    """更新供应商信息 - 对应 EditSupplierModal 的需求"""
    supplier_id = request.data.get('supplier_id')
    update_data = request.data.get('update_data', {})
    
    try:
        supplier = Supplier.objects.get(id=supplier_id)
        
        # 获取当前用户信息
        current_user = request.user.username if request.user.is_authenticated else '系统用户'
        
        # 只更新前端需要的字段
        allowed_fields = ['name', 'source', 'contact', 'store_name']
        for field in allowed_fields:
            if field in update_data:
                setattr(supplier, field, update_data[field])
        
        # 更新审计信息
        supplier.purchaser_updated_by = current_user
        
        supplier.save()
        
        # 更新商品信息
        if 'commodities' in update_data:
            for commodity_data in update_data['commodities']:
                if 'id' in commodity_data:
                    # 更新现有商品
                    try:
                        commodity = SupplierCommodity.objects.get(id=commodity_data['id'])
                        commodity.name = commodity_data.get('name', commodity.name)
                        commodity.specification = commodity_data.get('specification', commodity.specification)
                        commodity.price = commodity_data.get('price', commodity.price)
                        commodity.quantity = commodity_data.get('quantity', commodity.quantity)
                        commodity.product_url = commodity_data.get('product_url', commodity.product_url)
                        commodity.save()
                    except SupplierCommodity.DoesNotExist:
                        # 创建新商品
                        SupplierCommodity.objects.create(
                            supplier=supplier,
                            name=commodity_data.get('name', ''),
                            specification=commodity_data.get('specification', ''),
                            price=commodity_data.get('price', 0),
                            quantity=commodity_data.get('quantity', 1),
                            product_url=commodity_data.get('product_url', '')
                        )
        
        return create_success_response('供应商信息已更新')
        
    except Supplier.DoesNotExist:
        return create_error_response('供应商不存在', 404)
    except Exception as e:
        print(f"DEBUG: Unexpected error in update_supplier: {str(e)}")
        return create_error_response(f'服务器内部错误: {str(e)}', 500)

@api_view(['POST'])
def add_supplier(request):
    """添加供应商 - 完整修复版本"""
    print(f"DEBUG: add_supplier received data: {request.data}")
    
    try:
        project_id = request.data.get('project_id')
        supplier_data = request.data.get('supplier_data', {})
        
        if not project_id:
            return create_error_response('项目ID不能为空', 400)
        
        if not supplier_data:
            return create_error_response('供应商数据不能为空', 400)
        
        if not supplier_data.get('name'):
            return create_error_response('供应商名称不能为空', 400)
        
        # 使用 ProcurementPurchasing 直接查询
        purchasing = ProcurementPurchasing.objects.get(procurement_id=project_id, is_selected=True)
        
        # 获取当前用户信息
        current_user = request.user.username if request.user.is_authenticated else '系统用户'
        
        # 创建供应商 - 添加审计字段
        supplier = Supplier.objects.create(
            name=supplier_data.get('name', ''),
            source=supplier_data.get('source', ''),
            contact=supplier_data.get('contact', supplier_data.get('contact_info', '')),
            store_name=supplier_data.get('store_name', ''),
            # 添加审计字段
            purchaser_created_by=current_user,
            purchaser_updated_by=current_user
        )
        
        # 创建商品
        commodities_data = supplier_data.get('commodities', [])
        for commodity_data in commodities_data:
            SupplierCommodity.objects.create(
                supplier=supplier,
                name=commodity_data.get('name', ''),
                specification=commodity_data.get('specification', ''),
                price=commodity_data.get('price', 0),
                quantity=commodity_data.get('quantity', 1),
                product_url=commodity_data.get('product_url', '')
            )
        
        # 创建供应商关系 - 也添加审计字段
        ProcurementSupplier.objects.create(
            procurement=purchasing,
            supplier=supplier,
            is_selected=supplier_data.get('is_selected', False),
            purchaser_created_by=current_user,
            purchaser_updated_by=current_user
        )
        
        print(f"DEBUG: Successfully added supplier {supplier.id} for project {project_id}")
        print(f"DEBUG: Created by user: {current_user}")
        
        return create_success_response('供应商添加成功', {'supplier_id': supplier.id})
        
    except ProcurementPurchasing.DoesNotExist:
        return create_error_response('项目不存在或未被选中', 404)
    except Exception as e:
        print(f"DEBUG: Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_error_response(f'服务器内部错误: {str(e)}', 500)

@api_view(['POST'])
def delete_supplier(request):
    """删除供应商"""
    supplier_id = request.data.get('supplier_id')
    project_id = request.data.get('project_id')
    
    try:
        procurement = ProcurementEmall.objects.get(id=project_id)
        purchasing = procurement.purchasing_info
        
        # 删除供应商关系
        procurement_supplier = ProcurementSupplier.objects.get(
            procurement=purchasing,
            supplier_id=supplier_id
        )
        procurement_supplier.delete()
        
        # 如果该供应商没有其他关联，可以删除供应商本身（可选）
        if not ProcurementSupplier.objects.filter(supplier_id=supplier_id).exists():
            Supplier.objects.filter(id=supplier_id).delete()
        
        return create_success_response('供应商删除成功')
        
    except (ProcurementEmall.DoesNotExist, ProcurementPurchasing.DoesNotExist):
        return create_error_response('项目不存在', 404)
    except ProcurementSupplier.DoesNotExist:
        return create_error_response('供应商关系不存在', 404)
    except Exception as e:
        print(f"DEBUG: Unexpected error in delete_supplier: {str(e)}")
        return create_error_response(f'服务器内部错误: {str(e)}', 500)
