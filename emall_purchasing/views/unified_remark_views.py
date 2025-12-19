# emall_purchasing/views/unified_remark_views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ObjectDoesNotExist
import json
from ..models import UnifiedProcurementRemark, ProcurementPurchasing
from emall.models import ProcurementEmall
from .username_utils import get_username_from_request

@require_http_methods(["POST"])
@csrf_exempt
def add_unified_remark(request, procurement_id):
    """添加统一备注"""
    try:
        # 验证采购项目是否存在
        procurement = ProcurementEmall.objects.get(id=procurement_id)
        
        # 解析请求数据
        data = json.loads(request.body)
        remark_content = data.get('remark_content', '').strip()
        remark_type = data.get('remark_type', 'general')
        
        if not remark_content:
            return JsonResponse({
                'success': False,
                'error': '备注内容不能为空'
            }, status=400)
        
        # 验证备注类型
        valid_remark_types = ['general', 'purchasing', 'client']
        if remark_type not in valid_remark_types:
            remark_type = 'general'
        
        # 尝试获取采购进度信息（如果存在）
        purchasing_info = None
        try:
            purchasing_info = procurement.purchasing_info
        except ProcurementPurchasing.DoesNotExist:
            pass
        
        # 使用工具函数获取用户名
        username = get_username_from_request(request)
        
        # 获取用户角色（从cookie或session）
        user_role = request.COOKIES.get('userrole', '未知角色')  # 添加这行
        
        # 创建统一备注
        remark = UnifiedProcurementRemark.objects.create(
            procurement=procurement,
            purchasing=purchasing_info,
            remark_content=remark_content,
            created_by=username,
            created_role=user_role,  # 现在user_role已经定义
            remark_type=remark_type
        )
        
        return JsonResponse({
            'success': True,
            'message': '备注添加成功',
            'remark': {
                'id': remark.id,
                'remark_content': remark.remark_content,
                'created_by': remark.created_by,
                'created_role': remark.created_role,  # 添加角色信息
                'remark_type': remark.remark_type,
                'remark_type_display': remark.get_remark_type_display(),
                'created_at': remark.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'created_at_display': remark.created_at.strftime('%Y-%m-%d %H:%M')
            }
        })
        
    except ProcurementEmall.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '采购项目不存在'
        },status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'添加备注失败: {str(e)}'
        }, status=500)

@require_http_methods(["GET"])
def get_unified_remarks(request, procurement_id):
    """获取采购项目的统一备注列表"""
    try:
        # 验证采购项目是否存在
        procurement = ProcurementEmall.objects.get(id=procurement_id)
        
        # 获取备注列表，按创建时间倒序排列
        remarks = UnifiedProcurementRemark.objects.filter(
            procurement=procurement
        ).order_by('-created_at')
        
        remarks_data = []
        for remark in remarks:
            remarks_data.append({
                'id': remark.id,
                'remark_content': remark.remark_content,
                'created_by': remark.created_by,
                'remark_type': remark.remark_type,
                'remark_type_display': remark.get_remark_type_display(),
                'created_at': remark.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'created_at_display': remark.created_at.strftime('%Y-%m-%d %H:%M'),
                'updated_at': remark.updated_at.strftime('%Y-%m-%d %H:%M:%S') if remark.updated_at else None
            })
        
        return JsonResponse({
            'success': True,
            'remarks': remarks_data,
            'total_count': len(remarks_data)
        })
        
    except ProcurementEmall.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '采购项目不存在'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'获取备注列表失败: {str(e)}'
        }, status=500)

@require_http_methods(["DELETE"])
@csrf_exempt
def delete_unified_remark(request, remark_id):
    """删除统一备注"""
    try:
        # 验证备注是否存在
        remark = UnifiedProcurementRemark.objects.get(id=remark_id)
        
        # 使用工具函数获取当前用户名
        current_username = get_username_from_request(request)
        
        # 检查权限：只有创建者或管理员可以删除
        if remark.created_by != current_username and not (hasattr(request, 'user') and request.user.is_staff):
            return JsonResponse({
                'success': False,
                'error': '没有权限删除此备注'
            }, status=403)
        
        # 删除备注
        remark.delete()
        
        return JsonResponse({
            'success': True,
            'message': '备注删除成功'
        })
        
    except UnifiedProcurementRemark.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '备注不存在'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'删除备注失败: {str(e)}'
        }, status=500)
