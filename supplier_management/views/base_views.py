# supplier_management/views/base_views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response

def create_error_response(message, status=400):
    """创建统一错误响应"""
    return Response({'error': message}, status=status)

def create_success_response(message, data=None):
    """创建统一成功响应"""
    response = {'success': True, 'message': message}
    if data:
        response.update(data)
    return Response(response)
