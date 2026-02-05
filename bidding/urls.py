from django.urls import path
from .views import BiddingProjectListView, BiddingProjectDetailView, ProvinceStatsView

urlpatterns = [
    # 门户统计
    path('stats/provinces/', ProvinceStatsView.as_view(), name='province-stats'),
    
    # 列表筛选
    path('list/', BiddingProjectListView.as_view(), name='project-list'),
    
    # 详情展示 (修改这里：把 pk 改为 id)
    path('project/<int:id>/', BiddingProjectDetailView.as_view(), name='project-detail'),
]