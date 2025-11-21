from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.core.paginator import InvalidPage
from rest_framework.exceptions import NotFound

class DataTablesPagination(PageNumberPagination):
    """DataTables 分页类"""
    page_size = 25  # 与前端 pageLength 保持一致
    page_size_query_param = 'length'
    max_page_size = 500

    def get_paginated_response(self, data):
        return Response({
            "draw": int(self.request.query_params.get('draw', 1)),
            "recordsTotal": self.page.paginator.count,
            "recordsFiltered": self.page.paginator.count,
            "data": data
        })

    def paginate_queryset(self, queryset, request, view=None):
        # 手动处理 DataTables 的分页参数
        page_size = self.get_page_size(request)
        if not page_size:
            return None

        paginator = self.django_paginator_class(queryset, page_size)
        
        # DataTables 使用 start 参数，我们需要将其转换为页码
        start = request.query_params.get('start', 0)
        try:
            start = int(start)
            # 计算页码：start / page_size + 1
            page_number = (start // page_size) + 1
        except (TypeError, ValueError):
            page_number = 1

        try:
            self.page = paginator.page(page_number)
        except InvalidPage as exc:
            msg = self.invalid_page_message.format(
                page_number=page_number, message=str(exc)
            )
            raise NotFound(msg)

        if paginator.num_pages > 1 and self.template is not None:
            self.display_page_controls = True

        self.request = request
        return list(self.page)
