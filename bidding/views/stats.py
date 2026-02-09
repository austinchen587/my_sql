from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from django.utils import timezone
from ..models import BiddingProject
# [新增] 引入 UserProfile 以判断角色
# 请确保你的 UserProfile 定义在 authentication.models 中
try:
    from authentication.models import UserProfile
except ImportError:
    # 兜底，防止导入错误
    UserProfile = None

class ProvinceStatsView(generics.GenericAPIView):
    """
    门户接口：返回各省份的项目数量
    URL: /api/bidding/stats/province/
    """
    def get(self, request):
        data = BiddingProject.objects.values('province').annotate(count=Count('pk'))
        result = {item['province']: item['count'] for item in data}
        return Response(result)

class BiddingStatsView(APIView):
    """
    大厅统计接口：按子类目、归属人、状态统计
    权限：Admin看所有，普通用户只看自己
    URL: /api/bidding/stats/project/?province=JX
    """
    permission_classes = [IsAuthenticated] # [新增] 必须登录

    def get(self, request):
        now = timezone.now()
        province = request.query_params.get('province')
        user = request.user
        
        # [新增] 获取角色逻辑
        user_role = 'unassigned'
        if UserProfile:
            try:
                user_role = user.userprofile.role
            except Exception:
                pass
        
        # 1. 基础过滤：未过期 + 物资类 (goods)
        qs = BiddingProject.objects.filter(end_time__gt=now, root_category='goods')
        if province:
            qs = qs.filter(province=province)

        # [新增] 权限过滤：如果不是 admin，只看自己的项目
        if user_role != 'admin':
            # 假设 project_owner 存储的是 username
            qs = qs.filter(source_emall__purchasing_info__project_owner=user.username)

        # === 统计 1：物资子类目分布 ===
        sub_cats_def = dict(BiddingProject.SUB_CATS)
        
        # A. 基础统计
        sub_stats = qs.values('sub_category').annotate(
            total=Count('pk'),
            selected=Count('pk', filter=Q(source_emall__purchasing_info__is_selected=True))
        )
        sub_lookup = {item['sub_category']: item for item in sub_stats}

        # B. 归属人详情统计
        owner_stats = qs.filter(source_emall__purchasing_info__is_selected=True).values(
            'sub_category', 
            'source_emall__purchasing_info__project_owner'
        ).annotate(count=Count('pk'))

        category_owners_map = {}
        for item in owner_stats:
            cat = item['sub_category']
            owner = item['source_emall__purchasing_info__project_owner']
            if not owner: continue
            
            if cat not in category_owners_map: category_owners_map[cat] = []
            category_owners_map[cat].append({'name': owner, 'count': item['count']})

        # C. 组装数据
        sub_cats_data = []
        for key, label in sub_cats_def.items():
            stat = sub_lookup.get(key, {'total': 0, 'selected': 0})
            owners = category_owners_map.get(key, [])
            owners.sort(key=lambda x: x['count'], reverse=True)

            sub_cats_data.append({
                'key': key, 'label': label,
                'total': stat['total'], 'selected': stat['selected'],
                'unselected': stat['total'] - stat['selected'],
                'owners': owners
            })

        # === 统计 2：总状态分布 ===
        selected_qs = qs.filter(source_emall__purchasing_info__is_selected=True)
        status_data = selected_qs.values('source_emall__purchasing_info__bidding_status').annotate(count=Count('pk'))
        status_map = {item.get('source_emall__purchasing_info__bidding_status') or 'unknown': item['count'] for item in status_data}

        # === 统计 3：总归属人榜单 ===
        owner_data = selected_qs.values('source_emall__purchasing_info__project_owner').annotate(count=Count('pk')).order_by('-count')
        owners_list = [{'name': item['source_emall__purchasing_info__project_owner'], 'count': item['count']} for item in owner_data if item['source_emall__purchasing_info__project_owner']]

        return Response({
            "sub_cats": sub_cats_data,
            "status_dist": status_map,
            "owner_dist": owners_list,
            "user_role": user_role  # [新增] 返回角色给前端做展示判断
        })