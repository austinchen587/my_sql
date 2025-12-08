from .models import UserProfile

def get_user_role(user):
    """获取用户角色"""
    try:
        return user.userprofile.role
    except UserProfile.DoesNotExist:
        # 如果 UserProfile 不存在，创建默认的
        UserProfile.objects.create(user=user, role='unassigned')
        return 'unassigned'

def has_permission(user, required_role):
    """检查用户是否有权限"""
    user_role = get_user_role(user)
    return user_role == required_role or user_role == 'admin'
