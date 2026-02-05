from django.db.models.signals import post_save
from django.dispatch import receiver
from emall.models import ProcurementEmall
from .services import sync_single_project

@receiver(post_save, sender=ProcurementEmall)
def auto_sync_on_save(sender, instance, created, **kwargs):
    """
    监听器：当 ProcurementEmall 有新数据插入或修改时，自动同步到 BiddingProject
    """
    # 调用刚才写的服务进行同步
    sync_single_project(instance)