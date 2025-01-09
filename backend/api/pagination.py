from django.conf import settings

from rest_framework.pagination import LimitOffsetPagination


class PageToLimitOffsetPagination(LimitOffsetPagination):
    default_limit = settings.DEFAULT_PAGINATION_LIMIT
    max_limit = 100
    limit_query_param = 'limit'
    offset_query_param = 'offset'

    def paginate_queryset(self, queryset, request, view=None):
        page = request.query_params.get('page')
        limit = request.query_params.get(
            self.limit_query_param,
            self.default_limit
        )

        if page is not None:
            try:
                page = int(page)
                limit = int(limit)
                offset = (page - 1) * limit
                request.query_params._mutable = True
                request.query_params[self.offset_query_param] = offset
                request.query_params._mutable = False
            except ValueError:
                pass

        return super().paginate_queryset(queryset, request, view)
