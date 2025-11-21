# emall_purchasing/views/progress_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import ProcurementPurchasing

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
