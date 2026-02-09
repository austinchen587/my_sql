# bidding/urls.py

from django.urls import path
from .views import (
    BiddingProjectListView, 
    BiddingProjectDetailView, 
    ProvinceStatsView,
    BiddingStatsView
)
# [新增] 引入 emall_purchasing 中的备注视图
from emall_purchasing.views.remark_views import add_remark

urlpatterns = [
    path('stats/provinces/', ProvinceStatsView.as_view(), name='province-stats'),
    
    path('project/stats/', BiddingStatsView.as_view(), name='project-stats'),

    path('list/', BiddingProjectListView.as_view(), name='project-list'),
    path('project/<int:id>/', BiddingProjectDetailView.as_view(), name='project-detail'),

    # [关键修复] 注册前端请求的备注接口路由
    # 前端请求: /api/bidding/project/{id}/remark/
    # 注意参数名必须是 procurement_id 以匹配视图函数的参数定义
    path('project/<int:procurement_id>/remark/', add_remark, name='project-add-remark'),
]