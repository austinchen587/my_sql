from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'get_role', 'is_staff')
    
    def get_role(self, obj):
        try:
            return obj.userprofile.role
        except UserProfile.DoesNotExist:
            # 如果 UserProfile 不存在，创建默认的，角色为"未分配角色"
            UserProfile.objects.create(user=obj, role='unassigned')
            return 'unassigned'
    get_role.short_description = '角色'

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
