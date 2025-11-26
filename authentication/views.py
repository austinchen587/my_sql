# authentication/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .serializers import RegisterSerializer
import json
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
def user_login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            
            logger.info(f"登录请求 - 用户名: {username}")
            
            if not username or not password:
                return JsonResponse({
                    'status': 'error',
                    'message': '用户名和密码不能为空'
                }, status=400)
            
            user = authenticate(request, username=username,password=password)
            if user is not None:
                login(request, user)
                logger.info(f"用户登录成功: {username}")
                return JsonResponse({
                    'status': 'success',
                    'message': '登录成功',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email
                    }
                })
            else:
                logger.warning(f"登录失败 - 用户名或密码错误: {username}")
                return JsonResponse({
                    'status': 'error',
                    'message': '用户名或密码错误'
                }, status=400)
                
        except json.JSONDecodeError:
            logger.error("登录请求 - JSON格式错误")
            return JsonResponse({
                'status': 'error',
                'message': '请求格式错误'
            }, status=400)
        except Exception as e:
            logger.error(f"登录请求 - 系统错误: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': '系统错误，请稍后重试'
            }, status=500)
    else:
        logger.warning(f"登录请求 - 方法不允许: {request.method}")
        return JsonResponse({
            'status': 'error',
            'message': '请使用 POST 方法请求登录接口'
        }, status=405)

@csrf_exempt
def user_logout(request):
    if request.method == 'POST':
        try:
            username = request.user.username if request.user.is_authenticated else '未知用户'
            logout(request)
            logger.info(f"用户退出登录: {username}")
            return JsonResponse({
                'status': 'success',
                'message': '退出登录成功'
            })
        except Exception as e:
            logger.error(f"退出登录错误: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': '退出登录失败'
            }, status=500)
    else:
        logger.warning(f"退出登录请求 - 方法不允许: {request.method}")
        return JsonResponse({
            'status': 'error',
            'message': '请使用 POST 方法请求退出登录'
        }, status=405)

@csrf_exempt
def user_register(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            logger.info(f"注册请求 - 数据: {data}")
            
            # 使用序列化器验证数据
            serializer = RegisterSerializer(data=data)
            
            if serializer.is_valid():
                logger.info("序列化器验证通过")
                
                # 创建用户
                user = serializer.save()
                logger.info(f"用户创建成功: {user.username}")
                
                # 自动登录新用户
                login(request, user)
                logger.info(f"用户自动登录成功: {user.username}")
                
                return JsonResponse({
                    'status': 'success',
                    'message': '注册成功',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email
                    }
                })
            else:
                errors = serializer.errors
                logger.warning(f"序列化器验证失败: {errors}")
                
                # 更详细的错误消息处理
                error_messages = []
                for field, field_errors in errors.items():
                    for error in field_errors:
                        error_messages.append(f"{field}: {error}")
                
                return JsonResponse({
                    'status': 'error',
                    'message': '; '.join(error_messages),
                    'errors': errors
                }, status=400)
                
        except json.JSONDecodeError:
            logger.error("注册请求 - JSON格式错误")
            return JsonResponse({
                'status': 'error',
                'message': 'JSON格式错误'
            }, status=400)
        except Exception as e:
            logger.error(f"注册请求 - 系统错误: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f'注册失败: {str(e)}'
            }, status=500)
    else:
        logger.warning(f"注册请求 - 方法不允许: {request.method}")
        return JsonResponse({
            'status': 'error',
            'message': '请使用POST方法请求'
        }, status=405)

@csrf_exempt
def get_current_user(request):
    """获取当前用户信息"""
    if request.method == 'GET':
        try:
            if request.user.is_authenticated:
                return JsonResponse({
                    'status': 'success',
                    'user': {
                        'id': request.user.id,
                        'username': request.user.username,
                        'email': request.user.email
                    }
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': '用户未登录'
                }, status=401)
        except Exception as e:
            logger.error(f"获取用户信息错误: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': '获取用户信息失败'
            }, status=500)
    else:
        return JsonResponse({
            'status': 'error',
            'message': '请使用GET方法请求'
        }, status=405)
