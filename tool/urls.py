from django.urls import path
from .views.views_home import home
from .views.views_chat import chat
from .views.views_chat_list_sessions import list_sessions
from .views.views_chat_load_chat_from_file import load_chat_from_file
from .views.views_chat_save_chat_to_file import save_chat_to_file



urlpatterns = [
    path('',home,name='home'),
    path('chat/',chat,name='chat'),
    path('save_chat/', save_chat_to_file,name='save_chat'),
    path('load_chat/', load_chat_from_file,name='load_chat'),
    path('list-sessions/', list_sessions,name='list_sessions'),



]
