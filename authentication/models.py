from django.contrib.auth.models import User
from django.db import models

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('unassigned', '未分配角色'),  # 添加未分配角色选项
        ('admin', '管理员'),
        ('procurement_staff', '采购人员'),
        ('supplier_manager', '供应商管理员'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='unassigned')  # 修改默认值
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"
