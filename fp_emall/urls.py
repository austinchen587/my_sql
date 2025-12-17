from django.urls import path
from .views import fp_emall_list

app_name = 'fp_emall'

urlpatterns = [
    path('list/', fp_emall_list, name='list'),
]
