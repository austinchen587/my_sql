from django.apps import AppConfig

class BiddingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bidding'

    def ready(self):
        # 这一行非常重要！启动时加载信号
        import bidding.signals