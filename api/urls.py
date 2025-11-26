# api/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('hello/', views.hello_world, name='hello'),
    path('users/', views.user_list, name='user_list'),
    path('profile/', views.current_user_profile, name='current_user_profile'),
]
