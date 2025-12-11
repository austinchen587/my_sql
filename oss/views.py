# oss/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .utils import oss_manager
import json

@csrf_exempt
@require_http_methods(["GET"])
def test_connection(request):
    """测试OSS连接"""
    result = oss_manager.test_connection()
    return JsonResponse(result)

@csrf_exempt
@require_http_methods(["POST"])
def upload_test_file(request):
    """上传测试文件"""
    if 'file' not in request.FILES:
        return JsonResponse({'success': False, 'error': '没有上传文件'})
    
    file_obj = request.FILES['file']
    result = oss_manager.upload_file(file_obj, file_obj.name, 'test')
    return JsonResponse(result)

@csrf_exempt
@require_http_methods(["GET"])
def list_files(request):
    """列出文件"""
    prefix = request.GET.get('prefix', '')
    result = oss_manager.list_files(prefix)
    return JsonResponse(result)

@csrf_exempt
@require_http_methods(["POST"])
def delete_file(request):
    """删除文件"""
    data = json.loads(request.body)
    object_name = data.get('object_name')
    
    if not object_name:
        return JsonResponse({'success': False, 'error': '缺少object_name参数'})
    
    result = oss_manager.delete_file(object_name)
    return JsonResponse(result)
