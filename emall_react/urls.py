from django.urls import path
from . import views

app_name = 'emall_react'

urlpatterns = [
    # 采购项目列表API - 完整路径将是 /api/emall/list/
    path('emall/list/', views.EmallListView.as_view(), name='emall-list'),
]
