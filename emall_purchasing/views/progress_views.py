# emall_purchasing/views/progress_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from ..models import ProcurementPurchasing, ProcurementSupplier, ProcurementRemark, ClientContact  # 添加 ClientContact 导入
from .utils import build_client_contacts, build_suppliers_info, build_remarks_history, safe_json_loads
import logging
import traceback
from django.conf import settings

logger = logging.getLogger(__name__)

class ProcurementProgressView(APIView):
    """采购进度管理视图"""
    def get(self, request, procurement_id):
        """获取采购进度信息"""
        try:
            logger.info(f"开始获取采购进度信息，ID: {procurement_id}")
            
            purchasing_info = ProcurementPurchasing.objects.select_related(
                'procurement'
            ).prefetch_related(
                'suppliers',
                'suppliers__commodities',
                'remarks_history',
                'client_contacts'
            ).get(procurement_id=procurement_id)
            
            logger.info(f"成功获取采购信息: {purchasing_info}")
            
            # 构建响应数据
            total_budget = purchasing_info.get_total_budget()
            budget_total = float(total_budget) if total_budget else 0
            
            # 修复：传递正确的参数给 build_client_contacts
            response_data = {
                'procurement_id': procurement_id,
                'procurement_title': purchasing_info.procurement.project_title,
                'procurement_number': purchasing_info.procurement.project_number,
                'bidding_status': purchasing_info.bidding_status,
                'bidding_status_display': purchasing_info.get_bidding_status_display(),
                'client_contacts': build_client_contacts(purchasing_info),  # 保持单参数调用
                'total_budget': budget_total,
                'suppliers_info': build_suppliers_info(purchasing_info),
                'remarks_history': build_remarks_history(purchasing_info),
                'created_at': purchasing_info.created_at.isoformat() if purchasing_info.created_at else None,
                'updated_at': purchasing_info.updated_at.isoformat() if purchasing_info.updated_at else None,
            }
            
            logger.info(f"成功构建响应数据，供应商数量: {len(response_data['suppliers_info'])}, 备注数量: {len(response_data['remarks_history'])}")
            return Response(response_data)
            
        except ProcurementPurchasing.DoesNotExist:
            logger.error(f"采购进度信息不存在，ID: {procurement_id}")
            return Response({
                'error': '采购进度信息不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"获取数据失败，ID: {procurement_id}, 错误: {str(e)}", exc_info=True)
            return Response({
                'error': f'获取数据失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def update_purchasing_info(request, procurement_id):
    """更新采购进度信息"""
    try:
        logger.info(f"开始更新采购进度信息，ID: {procurement_id}")
        purchasing_info = ProcurementPurchasing.objects.get(procurement_id=procurement_id)
        
        data = safe_json_loads(request)
        if not data:
            return Response({'error': '无效的JSON数据'}, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"接收到的数据: {data}")
        
        # 更新基础信息
        if 'bidding_status' in data:
            purchasing_info.bidding_status = data['bidding_status']
            logger.info(f"更新竞标状态: {data['bidding_status']}")
        
        # 更新联系人信息
        if 'client_contacts' in data and isinstance(data['client_contacts'], list):
            logger.info(f"开始更新联系人信息，数量: {len(data['client_contacts'])}")
            # 删除现有联系人
            purchasing_info.client_contacts.all().delete()
            
            # 添加新联系人
            contact_count = 0
            for contact_data in data['client_contacts']:
                if contact_data.get('name') or contact_data.get('contact_info'):
                    ClientContact.objects.create(
                        purchasing=purchasing_info,
                        name=contact_data.get('name', ''),
                        contact_info=contact_data.get('contact_info', '')
                    )
                    contact_count += 1
                    logger.info(f"添加联系人: {contact_data.get('name')} - {contact_data.get('contact_info')}")
            
            logger.info(f"联系人更新完成，成功添加: {contact_count} 个联系人")
        
        purchasing_info.save()
        logger.info("基础信息更新成功")
        
        # 更新供应商选择状态
        if 'supplier_selection' in data and isinstance(data['supplier_selection'], list):
            logger.info(f"开始更新供应商选择状态，数量: {len(data['supplier_selection'])}")
            updated_count = 0
            for supplier_data in data['supplier_selection']:
                try:
                    supplier_id = supplier_data.get('supplier_id')
                    is_selected = supplier_data.get('is_selected', False)
                    
                    if supplier_id is not None:
                        procurement_supplier = ProcurementSupplier.objects.get(
                            procurement=purchasing_info,
                            supplier_id=supplier_id
                        )
                        procurement_supplier.is_selected = bool(is_selected)
                        procurement_supplier.save()
                        updated_count += 1
                        logger.info(f"供应商 {supplier_id} 选择状态更新为: {is_selected}")
                    else:
                        logger.warning("供应商ID为空，跳过")
                except ProcurementSupplier.DoesNotExist:
                    logger.warning(f"供应商关系不存在，supplier_id: {supplier_id}")
                    continue
                except Exception as e:
                    logger.error(f"更新供应商选择状态失败，supplier_id: {supplier_id}, 错误: {str(e)}")
                    continue
            logger.info(f"供应商选择状态更新完成，成功更新: {updated_count} 个")
        
        # 添加备注
        if 'new_remark' in data and data['new_remark']:
            remark_data = data['new_remark']
            logger.info(f"准备创建备注数据: {remark_data}")
            
            remark_content = remark_data.get('remark_content')
            created_by = remark_data.get('created_by')
            
            if remark_content and created_by:
                try:
                    new_remark = ProcurementRemark.objects.create(
                        purchasing=purchasing_info,
                        remark_content=remark_content.strip(),
                        created_by=created_by.strip()
                    )
                    logger.info(f"成功添加新备注，备注ID: {new_remark.id}")
                except Exception as e:
                    logger.error(f"创建备注失败: {str(e)}")
                    logger.error(traceback.format_exc())
                    raise e
            else:
                logger.warning(f"备注数据不完整")
        
        current_remarks_count = purchasing_info.remarks_history.count()
        logger.info(f"当前采购项目的备注总数: {current_remarks_count}")
        
        logger.info(f"成功更新采购进度信息，ID: {procurement_id}")
        return Response({
            'success': True, 
            'message': '采购信息更新成功',
            'remarks_count': current_remarks_count
        })
        
    except ProcurementPurchasing.DoesNotExist:
        logger.error(f"采购项目不存在，ID: {procurement_id}")
        return Response({'error': '采购项目不存在'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"更新采购进度信息失败，ID: {procurement_id}, 错误: {str(e)}")
        logger.error(traceback.format_exc())
        return Response({
            'error': f'更新失败: {str(e)}',
            'details': traceback.format_exc() if settings.DEBUG else None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
