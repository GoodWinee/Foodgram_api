from rest_framework.pagination import PageNumberPagination

from api.constants import PAGE_NUM


class LimitPagination(PageNumberPagination):
    """Кастомный пагинатор."""

    page_size = PAGE_NUM
    page_size_query_param = 'limit'
