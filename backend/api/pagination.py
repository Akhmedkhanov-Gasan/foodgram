from django.conf import settings
from rest_framework.pagination import LimitOffsetPagination


class PageToLimitOffsetPagination(LimitOffsetPagination):
    default_limit = settings.DEFAULT_PAGINATION_LIMIT
    max_limit = 100
    limit_query_param = 'limit'
    offset_query_param = 'offset'
