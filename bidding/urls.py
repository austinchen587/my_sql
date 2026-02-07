# bidding/urls.py

from django.urls import path
from .views import (
    BiddingProjectListView, 
    BiddingProjectDetailView, 
    ProvinceStatsView,
    BiddingStatsView  # [新增] 引入新的 View
)

urlpatterns = [
    path('stats/provinces/', ProvinceStatsView.as_view(), name='province-stats'),
    
    # [新增] 注册统计接口
    # 注意：这条路由必须放在 'project/<int:id>/' 之前，否则 'stats' 会被当成 id 解析
    path('project/stats/', BiddingStatsView.as_view(), name='project-stats'),

    path('list/', BiddingProjectListView.as_view(), name='project-list'),
    path('project/<int:id>/', BiddingProjectDetailView.as_view(), name='project-detail'),
]