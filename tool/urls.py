from django.urls import path
from .views.views_home import home
from .views.views_chat import chat

urlpatterns = [
    path('',home,name='home'),
    path('chat/',chat,name='chat'),
]
