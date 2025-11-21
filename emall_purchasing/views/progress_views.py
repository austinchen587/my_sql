# emall_purchasing/views/progress_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum
from ..models import ProcurementPurchasing, Supplier, SupplierCommodity, ProcurementSupplier, ProcurementRemark
import json
from rest_framework.decorators import api_view
import logging
from decimal import Decimal
import traceback  # 添加traceback用于详细错误日志
from django.conf import settings  # 添加这行导入

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
                'remarks_history'
            ).get(procurement_id=procurement_id)
            
            logger.info(f"成功获取采购信息: {purchasing_info}")
            
            # 构建客户联系人数组
            client_contacts = []
            if purchasing_info.client_contact and purchasing_info.client_phone:
                client_contacts.append({
                    'name': purchasing_info.client_contact,
                    'phone': purchasing_info.client_phone
                })
            
            # 构建供应商信息
            suppliers_info = []
            for supplier in purchasing_info.suppliers.all():
                # 获取关联关系中的选择状态
                supplier_rel = ProcurementSupplier.objects.filter(
                    procurement=purchasing_info,
                    supplier=supplier
                ).first()
                
                # 计算供应商总报价和商品信息
                total_quote = Decimal('0')
                commodities = []
                
                # 计算商品和总报价
                for commodity in supplier.commodities.all():
                    commodity_total = commodity.price * commodity.quantity
                    total_quote += commodity_total
                    commodities.append({
                        'id': commodity.id,
                        'name': commodity.name,
                        'specification': commodity.specification,
                        'price': float(commodity.price),
                        'quantity': commodity.quantity,
                        'product_url': commodity.product_url,
                        'total': float(commodity_total)
                    })
                
                # 计算利润（预算 - 总报价）
                total_budget = purchasing_info.get_total_budget()
                profit = Decimal('0')
                
                if total_budget:
                    try:
                        # 处理各种可能的类型：Decimal, int, float, str
                        if isinstance(total_budget, Decimal):
                            pass  # 已经是Decimal，不需要转换
                        elif isinstance(total_budget, (int, float)):
                            total_budget = Decimal(str(total_budget))
                        elif isinstance(total_budget, str):
                            total_budget = Decimal(total_budget)
                        else:
                            total_budget = Decimal('0')
                        
                        profit = total_budget - total_quote
                    except (ValueError, TypeError):
                        logger.warning(f"预算金额格式错误，使用默认值0: {total_budget}")
                        profit = Decimal('0')
                
                suppliers_info.append({
                    'id': supplier.id,
                    'name': supplier.name,
                    'source': supplier.source,
                    'contact': supplier.contact,
                    'store_name': supplier.store_name,
                    'commodities': commodities,
                    'total_quote': float(total_quote),
                    'profit': float(profit),
                    'is_selected': supplier_rel.is_selected if supplier_rel else False
                })
            
            # 构建备注历史 - 添加详细日志
            remarks_history = []
            all_remarks = purchasing_info.remarks_history.all().order_by('-created_at')
            logger.info(f"查询到的备注数量: {all_remarks.count()}")
            
            for remark in all_remarks:
                remarks_history.append({
                    'id': remark.id,
                    'remark_content': remark.remark_content,
                    'created_at': remark.created_at.isoformat(),
                    'created_at_display': remark.created_at.strftime('%Y-%m-%d %H:%M'),
                    'created_by': remark.created_by
                })
                logger.info(f"备注详情: ID={remark.id}, 内容={remark.remark_content}, 创建人={remark.created_by}")
            
            # 获取预算总额
            budget_total = purchasing_info.get_total_budget()
            if budget_total:
                try:
                    budget_total = float(budget_total)
                except (ValueError, TypeError):
                    budget_total = 0
            else:
                budget_total = 0
            
            response_data = {
                'procurement_id': procurement_id,
                'procurement_title': purchasing_info.procurement.project_title,
                'procurement_number': purchasing_info.procurement.project_number,
                'bidding_status': purchasing_info.bidding_status,
                'bidding_status_display': purchasing_info.get_bidding_status_display(),
                'client_contact': purchasing_info.client_contact or '',
                'client_phone': purchasing_info.client_phone or '',
                'client_contacts': client_contacts,
                'total_budget': budget_total,
                'suppliers_info': suppliers_info,
                'remarks_history': remarks_history,
                'created_at': purchasing_info.created_at.isoformat() if purchasing_info.created_at else None,
                'updated_at': purchasing_info.updated_at.isoformat() if purchasing_info.updated_at else None,
            }
            
            logger.info(f"成功构建响应数据，供应商数量: {len(suppliers_info)}, 备注数量: {len(remarks_history)}")
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
def add_supplier_to_procurement(request, procurement_id):
    """添加供应商到采购项目"""
    try:
        logger.info(f"开始添加供应商到采购项目，ID: {procurement_id}")
        purchasing_info = ProcurementPurchasing.objects.get(procurement_id=procurement_id)
        
        # 使用DRF的方式获取数据，更安全
        data = request.data if hasattr(request, 'data') else json.loads(request.body)
        
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
        
        logger.info(f"成功添加供应商: {supplier.name} 到采购项目: {procurement_id}")
        return Response({'success': True, 'message': '供应商添加成功'})
        
    except ProcurementPurchasing.DoesNotExist:
        logger.error(f"采购项目不存在，ID: {procurement_id}")
        return Response({'error': '采购项目不存在'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"添加供应商失败，ID: {procurement_id}, 错误: {str(e)}", exc_info=True)
        return Response({'error': f'添加失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def update_purchasing_info(request, procurement_id):
    """更新采购进度信息"""
    try:
        logger.info(f"开始更新采购进度信息，ID: {procurement_id}")
        purchasing_info = ProcurementPurchasing.objects.get(procurement_id=procurement_id)
        
        # 使用DRF的方式获取数据，更安全
        if hasattr(request, 'data'):
            data = request.data
        else:
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析错误: {e}")
                return Response({'error': '无效的JSON数据'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 添加详细的请求数据日志
        logger.info(f"接收到的数据: {json.dumps(data, ensure_ascii=False, default=str)}")
        
        # 更新基础信息 - 添加空值处理
        if 'bidding_status' in data:
            purchasing_info.bidding_status = data['bidding_status']
            logger.info(f"更新竞标状态: {data['bidding_status']}")
        
        if 'client_contact' in data:
            purchasing_info.client_contact = data['client_contact'] or ''
            logger.info(f"更新甲方联系人: {data['client_contact']}")
        
        if 'client_phone' in data:
            purchasing_info.client_phone = data['client_phone'] or ''
            logger.info(f"更新甲方联系方式: {data['client_phone']}")
            
        purchasing_info.save()
        logger.info("基础信息更新成功")
        
        # 更新供应商选择状态 - 添加更安全的处理
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
        
        # 添加备注 - 确保正确处理备注数据
        if 'new_remark' in data and data['new_remark']:
            remark_data = data['new_remark']
            logger.info(f"准备创建备注数据: {remark_data}")
            
            # 详细检查备注数据字段
            remark_content = remark_data.get('remark_content')
            created_by = remark_data.get('created_by')
            
            logger.info(f"备注内容是否存在: {remark_content is not None}")
            logger.info(f"创建人是否存在: {created_by is not None}")
            logger.info(f"备注内容是否为空字符串: {remark_content == ''}")
            logger.info(f"创建人是否为空字符串: {created_by == ''}")
            
            if remark_content and created_by:
                try:
                    new_remark = ProcurementRemark.objects.create(
                        purchasing=purchasing_info,
                        remark_content=remark_content.strip(),
                        created_by=created_by.strip()
                    )
                    logger.info(f"成功添加新备注，备注ID: {new_remark.id}, 内容长度: {len(remark_content)}")
                except Exception as e:
                    logger.error(f"创建备注失败: {str(e)}")
                    logger.error(traceback.format_exc())
                    raise e
            else:
                logger.warning(f"备注数据不完整，内容: '{remark_content}', 创建人: '{created_by}'")
        else:
            logger.info("没有新的备注数据")
        
        # 验证备注是否真的创建了
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
        logger.error(traceback.format_exc())  # 添加详细错误堆栈
        return Response({
            'error': f'更新失败: {str(e)}',
            'details': traceback.format_exc() if settings.DEBUG else None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
        logger.error(f"删除供应商失败，ID: {supplier_id}, 错误: {str(e)}", exc_info=True)
        return Response({'error': f'删除失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['PUT'])
def update_supplier(request, supplier_id):
    """更新供应商信息"""
    try:
        logger.info(f"开始更新供应商信息，ID: {supplier_id}")
        supplier = Supplier.objects.get(id=supplier_id)
        data = request.data if hasattr(request, 'data') else json.loads(request.body)
        
        # 更新供应商基本信息
        supplier.name = data.get('name', supplier.name)
        supplier.source = data.get('source', supplier.source)
        supplier.contact = data.get('contact', supplier.contact)
        supplier.store_name = data.get('store_name', supplier.store_name)
        supplier.save()
        
        # 更新关联的选择状态
        procurement_supplier = ProcurementSupplier.objects.filter(supplier=supplier).first()
        if procurement_supplier:
            procurement_supplier.is_selected = data.get('is_selected', False)
            procurement_supplier.save()
        
        # 删除旧商品并创建新商品
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
        
        logger.info(f"成功更新供应商信息，ID: {supplier_id}")
        return Response({'success': True, 'message': '供应商更新成功'})
        
    except Supplier.DoesNotExist:
        logger.error(f"供应商不存在，ID: {supplier_id}")
        return Response({'error': '供应商不存在'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"更新供应商失败，ID: {supplier_id}, 错误: {str(e)}", exc_info=True)
        return Response({'error': f'更新失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
