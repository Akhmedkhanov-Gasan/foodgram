from rest_framework.pagination import LimitOffsetPagination


class PageToLimitOffsetPagination(LimitOffsetPagination):
    def paginate_queryset(self, queryset, request, view=None):
        page = request.query_params.get('page')
        limit = request.query_params.get('limit', self.default_limit)

        if page is not None:
            offset = (int(page) - 1) * int(limit)
            request.query_params._mutable = True
            request.query_params['offset'] = offset
            request.query_params._mutable = False

        return super().paginate_queryset(queryset, request, view)
