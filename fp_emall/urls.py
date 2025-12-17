from django.urls import path
from .views import fp_emall_list, fp_emall_search, get_search_fields

app_name = 'fp_emall'

urlpatterns = [
    path('list/', fp_emall_list, name='list'),
    path('search/', fp_emall_search, name='search'),
    path('search-fields/', get_search_fields, name='fp_emall_search_fields'),
]
