# emall_react/pagination.py
from rest_framework.pagination import PageNumberPagination

class EmallPagination(PageNumberPagination):
    page_size = 100  # 每页显示100条
    page_size_query_param = 'page_size'
    max_page_size = 500
