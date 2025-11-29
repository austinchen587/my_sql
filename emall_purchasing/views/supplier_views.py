# emall_purchasing/views/supplier_views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from ..models import ProcurementPurchasing, Supplier, SupplierCommodity, ProcurementSupplier
from .utils import safe_json_loads
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
def add_supplier_to_procurement(request, procurement_id):
    """添加供应商到采购项目"""
    try:
        logger.info(f"开始添加供应商到采购项目，ID: {procurement_id}")
        purchasing_info = ProcurementPurchasing.objects.get(procurement_id=procurement_id)
        data = safe_json_loads(request)
        
        if not data:
            return Response({'error': '无效的JSON数据'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 创建供应商和商品
        supplier = Supplier.objects.create(
            name=data['name'],
            source=data.get('source', ''),
            contact=data.get('contact', ''),
            store_name=data.get('store_name', '')
        )
        
        for commodity_data in data.get('commodities', []):
            SupplierCommodity.objects.create(
                supplier=supplier,
                name=commodity_data['name'],
                specification=commodity_data.get('specification', ''),
                price=commodity_data['price'],
                quantity=commodity_data['quantity'],
                product_url=commodity_data.get('product_url', '')
            )
        
        ProcurementSupplier.objects.create(
            procurement=purchasing_info,
            supplier=supplier,
            is_selected=data.get('is_selected', False)
        )
        
        logger.info(f"成功添加供应商: {supplier.name}")
        return Response({'success': True, 'message': '供应商添加成功'})
        
    except ProcurementPurchasing.DoesNotExist:
        logger.error(f"采购项目不存在，ID: {procurement_id}")
        return Response({'error': '采购项目不存在'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"添加供应商失败，错误: {str(e)}", exc_info=True)
        return Response({'error': f'添加失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
def delete_supplier(request, supplier_id):
    """删除供应商"""
    try:
        logger.info(f"开始删除供应商，ID: {supplier_id}")
        supplier = Supplier.objects.get(id=supplier_id)
        supplier_name = supplier.name
        supplier.delete()
        logger.info(f"成功删除供应商: {supplier_name}")
        return Response({'success': True, 'message': '供应商删除成功'})
    except Supplier.DoesNotExist:
        logger.error(f"供应商不存在，ID: {supplier_id}")
        return Response({'error': '供应商不存在'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"删除供应商失败，错误: {str(e)}", exc_info=True)
        return Response({'error': f'删除失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
def update_supplier(request, supplier_id):
    """更新供应商信息"""
    try:
        logger.info(f"开始更新供应商信息，ID: {supplier_id}")
        supplier = Supplier.objects.get(id=supplier_id)
        data = safe_json_loads(request)
        
        if not data:
            return Response({'error': '无效的JSON数据'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 更新供应商信息
        supplier.name = data.get('name', supplier.name)
        supplier.source = data.get('source', supplier.source)
        supplier.contact = data.get('contact', supplier.contact)
        supplier.store_name = data.get('store_name', supplier.store_name)
        supplier.save()
        
        # 更新选择状态
        procurement_supplier = ProcurementSupplier.objects.filter(supplier=supplier).first()
        if procurement_supplier:
            procurement_supplier.is_selected = data.get('is_selected', False)
            procurement_supplier.save()
        
        # 更新商品信息
        supplier.commodities.all().delete()
        for commodity_data in data.get('commodities', []):
            SupplierCommodity.objects.create(
                supplier=supplier,
                name=commodity_data['name'],
                specification=commodity_data.get('specification', ''),
                price=commodity_data['price'],
                quantity=commodity_data['quantity'],
                product_url=commodity_data.get('product_url', '')
            )
        
        logger.info(f"成功更新供应商信息")
        return Response({'success': True, 'message': '供应商更新成功'})
        
    except Supplier.DoesNotExist:
        logger.error(f"供应商不存在，ID: {supplier_id}")
        return Response({'error': '供应商不存在'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"更新供应商失败，错误: {str(e)}", exc_info=True)
        return Response({'error': f'更新失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
