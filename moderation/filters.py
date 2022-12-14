from django_filters import OrderingFilter, FilterSet
from django.db.models import Count


class ReportOrderingFilter(OrderingFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extra['choices'] += (
            ('vote_count', "Vote count"),
            ('newest', "Newest")
        )

    def filter(self, qs, value):
        if value:
            for v in value:
                if v == 'vote_count':
                    return qs.annotate(vote_count=Count('voters')).order_by('-vote_count')
                if v == 'newest':
                    return qs.order_by('-pk')
        return super().filter(qs, value)


class ReportFilter(FilterSet):
    sort_by = ReportOrderingFilter()

