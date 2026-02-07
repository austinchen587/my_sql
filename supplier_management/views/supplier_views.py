# supplier_management/views/project_views.py

# supplier_management/views/supplier_views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from emall_purchasing.models import ProcurementPurchasing, ProcurementSupplier, Supplier, SupplierCommodity
from emall.models import ProcurementEmall
# [核心修复] 务必确保这里导入了 create_success_response
from .base_views import create_error_response, create_success_response
from bidding.models import ProcurementCommodityResult  # 引入 AI 结果模型
import json
import logging
import re # [新增] 用于提取数字
logger = logging.getLogger(__name__)

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
        
        # 更新商品信息 - 修复：添加支付金额和物流单号
        if 'commodities' in update_data:
            # 获取前端传来的商品ID列表
            new_commodity_ids = [c['id'] for c in update_data['commodities'] if 'id' in c]
            
            # 删除不在新列表中的商品
            existing_commodities = SupplierCommodity.objects.filter(supplier=supplier)
            commodities_to_delete = existing_commodities.exclude(id__in=new_commodity_ids)
            
            print(f"[DEBUG] Commodities to delete: {list(commodities_to_delete.values_list('id', flat=True))}")
            deleted_count = commodities_to_delete.delete()[0]
            print(f"[DEBUG] Deleted {deleted_count} commodities")
            
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
                        
                        # 🔥 修复：添加支付金额和物流单号的更新
                        commodity.payment_amount = commodity_data.get('payment_amount', commodity.payment_amount)
                        commodity.tracking_number = commodity_data.get('tracking_number', commodity.tracking_number)
                        
                        commodity.save()
                        
                        print(f"DEBUG: Updated commodity {commodity.id} with payment_amount: {commodity.payment_amount}, tracking_number: {commodity.tracking_number}")
                        
                    except SupplierCommodity.DoesNotExist:
                        # 创建新商品 - 同样需要包含支付金额和物流单号
                        SupplierCommodity.objects.create(
                            supplier=supplier,
                            name=commodity_data.get('name', ''),
                            specification=commodity_data.get('specification', ''),
                            price=commodity_data.get('price', 0),
                            quantity=commodity_data.get('quantity', 1),
                            product_url=commodity_data.get('product_url', ''),
                            # 🔥 修复：添加支付金额和物流单号
                            payment_amount=commodity_data.get('payment_amount', 0),
                            tracking_number=commodity_data.get('tracking_number', '')
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

@api_view(['POST'])
def toggle_supplier_selection(request):
    """切换供应商选择状态"""
    supplier_id = request.data.get('supplier_id')
    project_id = request.data.get('project_id')
    is_selected = request.data.get('is_selected')
    
    # print(f"DEBUG: toggle_selection - project_id: {project_id}, supplier_id: {supplier_id}, is_selected: {is_selected}")
    
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
        
        return create_success_response(f'供应商{"已选择" if is_selected else "已取消选择"}')
        
    except ProcurementPurchasing.DoesNotExist:
        return create_error_response('项目不存在或未被选中', 404)
    except ProcurementSupplier.DoesNotExist:
        return create_error_response('供应商关系不存在', 404)
    except Exception as e:
        logger.error(f"Toggle selection error: {e}")
        return create_error_response(f'服务器内部错误: {str(e)}', 500)

@api_view(['POST'])
def update_supplier(request):
    """更新供应商信息"""
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
        
        # 更新商品信息 - 修复：添加支付金额和物流单号
        if 'commodities' in update_data:
            # 获取前端传来的商品ID列表
            new_commodity_ids = [c['id'] for c in update_data['commodities'] if 'id' in c]
            
            # 删除不在新列表中的商品
            existing_commodities = SupplierCommodity.objects.filter(supplier=supplier)
            commodities_to_delete = existing_commodities.exclude(id__in=new_commodity_ids)
            
            # print(f"[DEBUG] Commodities to delete: {list(commodities_to_delete.values_list('id', flat=True))}")
            commodities_to_delete.delete()
            
            for commodity_data in update_data['commodities']:
                # 修复：确保 commodity_data 是字典
                if not isinstance(commodity_data, dict):
                    continue

                if 'id' in commodity_data and commodity_data['id']:
                    # 更新现有商品
                    try:
                        commodity = SupplierCommodity.objects.get(id=commodity_data['id'])
                        commodity.name = commodity_data.get('name', commodity.name)
                        commodity.specification = commodity_data.get('specification', commodity.specification)
                        
                        # 安全处理价格和数量
                        try:
                            commodity.price = float(commodity_data.get('price', 0))
                        except:
                            pass
                            
                        try:
                            commodity.quantity = int(commodity_data.get('quantity', 0))
                        except:
                            pass
                            
                        commodity.product_url = commodity_data.get('product_url', commodity.product_url)
                        
                        # 🔥 修复：添加支付金额和物流单号的更新
                        pay_amount = commodity_data.get('payment_amount')
                        if pay_amount is not None and pay_amount != '':
                            try:
                                commodity.payment_amount = float(pay_amount)
                            except:
                                pass
                        
                        track_no = commodity_data.get('tracking_number')
                        if track_no is not None:
                            commodity.tracking_number = str(track_no)
                        
                        commodity.save()
                        
                    except SupplierCommodity.DoesNotExist:
                        pass
                else:
                    # 创建新商品
                    try:
                        SupplierCommodity.objects.create(
                            supplier=supplier,
                            name=commodity_data.get('name', ''),
                            specification=commodity_data.get('specification', ''),
                            price=float(commodity_data.get('price', 0)) if commodity_data.get('price') else 0,
                            quantity=int(commodity_data.get('quantity', 1)) if commodity_data.get('quantity') else 1,
                            product_url=commodity_data.get('product_url', ''),
                            payment_amount=float(commodity_data.get('payment_amount', 0)) if commodity_data.get('payment_amount') else 0,
                            tracking_number=commodity_data.get('tracking_number', '')
                        )
                    except Exception as e:
                        logger.error(f"创建商品失败: {e}")
        
        return create_success_response('供应商信息已更新')
        
    except Supplier.DoesNotExist:
        return create_error_response('供应商不存在', 404)
    except Exception as e:
        logger.error(f"Update supplier error: {e}")
        return create_error_response(f'服务器内部错误: {str(e)}', 500)

@api_view(['POST'])
def add_supplier(request):
    """添加供应商"""
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
        
        # 创建供应商
        supplier = Supplier.objects.create(
            name=supplier_data.get('name', ''),
            source=supplier_data.get('source', '手动添加'),
            contact=supplier_data.get('contact', supplier_data.get('contact_info', '')),
            store_name=supplier_data.get('store_name', ''),
            purchaser_created_by=current_user,
            purchaser_updated_by=current_user
        )
        
        # 创建商品
        commodities_data = supplier_data.get('commodities', [])
        for commodity_data in commodities_data:
            try:
                SupplierCommodity.objects.create(
                    supplier=supplier,
                    name=commodity_data.get('name', ''),
                    specification=commodity_data.get('specification', ''),
                    price=float(commodity_data.get('price', 0)) if commodity_data.get('price') else 0,
                    quantity=int(commodity_data.get('quantity', 1)) if commodity_data.get('quantity') else 1,
                    product_url=commodity_data.get('product_url', '')
                )
            except Exception as e:
                logger.error(f"添加商品失败: {e}")
        
        # 创建供应商关系
        ProcurementSupplier.objects.create(
            procurement=purchasing,
            supplier=supplier,
            is_selected=supplier_data.get('is_selected', False),
            purchaser_created_by=current_user,
            purchaser_updated_by=current_user
        )
        
        return create_success_response('供应商添加成功', {'supplier_id': supplier.id})
        
    except ProcurementPurchasing.DoesNotExist:
        return create_error_response('项目不存在或未被选中', 404)
    except Exception as e:
        logger.error(f"Add supplier error: {e}")
        return create_error_response(f'服务器内部错误: {str(e)}', 500)

@api_view(['POST'])
def delete_supplier(request):
    """删除供应商"""
    supplier_id = request.data.get('supplier_id')
    project_id = request.data.get('project_id')
    
    try:
        # 兼容处理：可能传的是 procurement_id (string) 或 id (int)
        # 我们假设 project_id 是 procurement_id，先尝试查 Purchasing
        try:
            purchasing = ProcurementPurchasing.objects.get(procurement_id=project_id, is_selected=True)
        except:
            # 如果失败，可能传的是 emall_id
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
        logger.error(f"Delete supplier error: {e}")
        return create_error_response(f'服务器内部错误: {str(e)}', 500)