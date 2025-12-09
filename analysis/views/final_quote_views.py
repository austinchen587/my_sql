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
        data = request.data
        project_name = data.get('project_name')
        final_quote = data.get('final_quote')
        modified_by = data.get('modified_by')
        modified_role = data.get('modified_role')
        
        if not all([project_name, final_quote is not None, modified_by]):
            return Response({
                'success': False,
                'error': '缺少必要参数'
            }, status=400)
        
        with transaction.atomic():
            # 使用ORM方式更新，更安全
            updated_count = ProcurementSupplier.objects.filter(
                procurement__procurement__project_name=project_name,
                is_selected=True
            ).update(
                final_negotiated_quote=final_quote,
                final_quote_modified_by=modified_by,
                final_quote_modified_role=modified_role,
                final_quote_modified_at=timezone.now()
            )
                
            if updated_count == 0:
                return Response({
                    'success': False,
                    'error': '未找到对应的采购项目或选中的供应商'
                }, status=404)
            
            return Response({
                'success': True,
                'message': '最终报价更新成功',
                'updated_count': updated_count
            })
            
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)
