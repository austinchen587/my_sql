# api/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json

@csrf_exempt
def hello_world(request):
    if request.method == 'GET':
        return JsonResponse({
            'message': 'Hello from Django!', 
            'status': 'success'
        })

@csrf_exempt  
@login_required
def user_list(request):
    if request.method == 'GET':
        # 示例数据 - 替换为你的实际数据
        users = [
            {
                'id': 1,
                'name': '张三',
                'email': 'zhangsan@example.com',
                'created_at': '2023-01-01'
            },
            {
                'id': 2, 
                'name': '李四',
                'email': 'lisi@example.com',
                'created_at': '2023-01-02'
            }
        ]
        return JsonResponse(users, safe=False)

@csrf_exempt  
@login_required
def current_user_profile(request):
    if request.method == 'GET':
        user_data = {
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email
        }
        return JsonResponse({
            'user': user_data,
            'status': 'success'
        })
