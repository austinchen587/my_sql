# emall_purchasing/views/progress_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import ProcurementPurchasing
from ..models import ProcurementPurchasing, Supplier, SupplierCommodity, ProcurementSupplier, ProcurementRemark
import json
from rest_framework.decorators import api_view


class ProcurementProgressView(APIView):
    """采购进度管理视图"""
    
    def get(self,request, procurement_id):
        """获取采购进度信息"""
        try:
            purchasing_info = ProcurementPurchasing.objects.select_related(
                'procurement'
            ).prefetch_related(
                'suppliers',
                'remarks_history'  # 改为正确的关联名称
            ).get(procurement_id = procurement_id)
            
            # 构建供应商信息
            suppliers_info = []
            for supplier in purchasing_info.suppliers.all():
                # 获取关联关系中的选择状态
                supplier_rel = supplier.procurementsupplier_set.filter(
                    procurement=purchasing_info
                ).first()
                
                # 获取供应商商品信息
                commodities = []
                if hasattr(supplier, 'commodities'):
                    for commodity in supplier.commodities.all():
                        commodities.append({
                            'name': commodity.name,
                            'specification': commodity.specification,
                            'price': str(commodity.price),
                            'quantity': commodity.quantity,
                            'product_url': commodity.product_url
                        })
                
                suppliers_info.append({
                    'id': supplier.id,
                    'name': supplier.name,
                    'source': supplier.source,
                    'contact': supplier.contact,
                    'store_name': supplier.store_name,
                    'commodities': commodities,
                    'is_selected': supplier_rel.is_selected if supplier_rel else False
                })
            
            # 构建备注历史 - 使用正确的关联名称
            remarks_history = []
            for remark in purchasing_info.remarks_history.all().order_by('-created_at'):
                remarks_history.append({
                    'content': remark.remark_content,  # 注意字段名改为 remark_content
                    'created_at': remark.created_at,
                    'created_at_display': remark.created_at.strftime('%Y-%m-%d %H:%M'),  # 添加格式化时间
                    'created_by': remark.created_by  # 这里已经是字符串，不需要.username
                })
            
            response_data = {
                'procurement_id': procurement_id,
                'procurement_title': purchasing_info.procurement.project_title,
                'procurement_number': purchasing_info.procurement.project_number,
                'bidding_status': purchasing_info.bidding_status,
                'bidding_status_display': purchasing_info.get_bidding_status_display(),
                'client_contact': purchasing_info.client_contact or '',
                'client_phone': purchasing_info.client_phone or '',
                'total_budget': str(purchasing_info.get_total_budget()),
                'suppliers_info': suppliers_info,
                'remarks_history': remarks_history,
                'created_at': purchasing_info.created_at,
                'updated_at': purchasing_info.updated_at,
                'is_selected': purchasing_info.is_selected
            }
            
            return Response(response_data)
            
        except ProcurementPurchasing.DoesNotExist:
            return Response({
                'error': '采购进度信息不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'获取数据失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






@api_view(['POST'])
def add_supplier_to_procurement(request, procurement_id):
    """添加供应商到采购项目"""
    try:
        purchasing_info = ProcurementPurchasing.objects.get(procurement_id=procurement_id)
        data = json.loads(request.body)
        
        # 创建供应商
        supplier = Supplier.objects.create(
            name=data['name'],
            source=data.get('source', ''),
            contact=data.get('contact', ''),
            store_name=data.get('store_name', '')
        )
        
        # 创建商品
        for commodity_data in data.get('commodities', []):
            SupplierCommodity.objects.create(
                supplier=supplier,
                name=commodity_data['name'],
                specification=commodity_data.get('specification', ''),
                price=commodity_data['price'],
                quantity=commodity_data['quantity'],
                product_url=commodity_data.get('product_url', '')
            )
        
        # 关联供应商到采购项目
        ProcurementSupplier.objects.create(
            procurement=purchasing_info,
            supplier=supplier,
            is_selected=data.get('is_selected', False)
        )
        
        return Response({'success': True, 'message': '供应商添加成功'})
        
    except ProcurementPurchasing.DoesNotExist:
        return Response({'error': '采购项目不存在'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': f'添加失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
@api_view(['POST'])
def update_purchasing_info(request, procurement_id):
    """更新采购进度信息"""
    try:
        purchasing_info = ProcurementPurchasing.objects.get(procurement_id=procurement_id)
        data = json.loads(request.body)
        
        # 更新基础信息
        if 'bidding_status' in data:
            purchasing_info.bidding_status = data['bidding_status']
        if 'client_contact' in data:
            purchasing_info.client_contact = data['client_contact']
        if 'client_phone' in data:
            purchasing_info.client_phone = data['client_phone']
        if 'is_selected' in data:
            purchasing_info.is_selected = data['is_selected']
            
        purchasing_info.save()
        
        # 更新供应商选择状态
        if 'supplier_selection' in data:
            for supplier_data in data['supplier_selection']:
                try:
                    procurement_supplier = ProcurementSupplier.objects.get(
                        procurement=purchasing_info,
                        supplier_id=supplier_data['supplier_id']
                    )
                    procurement_supplier.is_selected = supplier_data['is_selected']
                    procurement_supplier.save()
                except ProcurementSupplier.DoesNotExist:
                    continue
        
        # 添加备注
        if 'new_remark' in data:
            remark_data = data['new_remark']
            if remark_data.get('content') and remark_data.get('created_by'):
                ProcurementRemark.objects.create(
                    purchasing=purchasing_info,
                    remark_content=remark_data['content'],
                    created_by=remark_data['created_by']
                )
        
        return Response({'success': True, 'message': '采购信息更新成功'})
        
    except ProcurementPurchasing.DoesNotExist:
        return Response({'error': '采购项目不存在'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': f'更新失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
@api_view(['DELETE'])
def delete_supplier(request, supplier_id):
    """删除供应商"""
    try:
        supplier = Supplier.objects.get(id=supplier_id)
        supplier.delete()
        return Response({'success': True, 'message': '供应商删除成功'})
    except Supplier.DoesNotExist:
        return Response({'error': '供应商不存在'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': f'删除失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)