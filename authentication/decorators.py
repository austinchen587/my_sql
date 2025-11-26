# authentication/decorators.py
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny

def login_required(view_func):
    """需要登录的装饰器"""
    return permission_classes([IsAuthenticated])(view_func)

def public_access(view_func):
    """公开访问的装饰器"""
    return permission_classes([AllowAny])(view_func)
