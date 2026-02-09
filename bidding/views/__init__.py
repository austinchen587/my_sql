# 必须从当前目录的 base 模块导入，而不是从其他地方
from .base import BiddingProjectListView, BiddingProjectDetailView
from .stats import ProvinceStatsView, BiddingStatsView
from .sync import sync_province_data