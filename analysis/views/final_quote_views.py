# analysis/views/final_quote_views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction
from emall_purchasing.models import ProcurementSupplier  # 正确的导入路径

@api_view(['POST'])
def update_final_quote(request):
    """更新最终报价并记录审计信息"""
    try:
        print("=== 收到更新最终报价请求 ===")
        print("请求数据:", request.data)
        
        data = request.data
        project_name = data.get('project_name')
        final_quote = data.get('final_quote')
        modified_by = data.get('modified_by')
        modified_role = data.get('modified_role')
        
        print(f"参数: project_name={project_name}, final_quote={final_quote}")
        
        if not all([project_name, final_quote is not None, modified_by]):
            return Response({
                'success': False,
                'error': '缺少必要参数'
            }, status=400)
        
        with transaction.atomic():
            # 新增：先检查项目是否存在
            from emall.models import ProcurementEmall
            project_exists = ProcurementEmall.objects.filter(project_name=project_name).exists()
            
            if not project_exists:
                return Response({
                    'success': False,
                    'error': f'项目 "{project_name}" 不存在于采购项目中'
                }, status=404)
            
            # 修改查询逻辑：通过 procurement_purchasing 表关联
            updated_count = ProcurementSupplier.objects.filter(
                procurement__procurement__project_name=project_name,
                is_selected=True
            ).update(
                final_negotiated_quote=final_quote,
                final_quote_modified_by=modified_by,
                final_quote_modified_role=modified_role,
                final_quote_modified_at=timezone.now()
            )
            
            print(f"查询条件: procurement__procurement__project_name='{project_name}', is_selected=True")
            print(f"更新记录数量: {updated_count}")
            
            if updated_count == 0:
                # 详细调试信息
                all_relations = ProcurementSupplier.objects.filter(
                    procurement__procurement__project_name=project_name
                )
                print(f"该项目所有供应商关系数量: {all_relations.count()}")
                
                for rel in all_relations:
                    print(f"供应商: {rel.supplier.name if rel.supplier else 'None'}, "
                          f"是否选中: {rel.is_selected}, "
                          f"采购ID: {rel.procurement.id if rel.procurement else 'None'}")
                
                return Response({
                    'success': False,
                    'error': f'项目存在但没有选中的供应商',
                    'debug_info': {
                        'project_exists': True,
                        'supplier_relations_count': all_relations.count(),
                        'selected_suppliers_count': all_relations.filter(is_selected=True).count()
                    }
                }, status=404)
            
            return Response({
                'success': True,
                'message': f'最终报价更新成功，更新了 {updated_count} 条记录',
                'updated_count': updated_count
            })
            
    except Exception as e:
        import traceback
        print(f"=== 发生异常 ===")
        print(traceback.format_exc())
        
        return Response({
            'success': False,
            'error': f"服务器内部错误: {str(e)}"
        }, status=500)