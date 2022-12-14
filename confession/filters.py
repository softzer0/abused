from django_filters import OrderingFilter, FilterSet
from django.db.models.functions import Coalesce


class ConfessionOrderingFilter(OrderingFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extra['choices'] += (
            ('popularity', "Popularity"),
            ('most_reactions', "Most reactions"),
            ('most_comments', "Most comments"),
            ('oldest', "Oldest"),
        )

    def filter(self, qs, value):
        if value:
            for v in value:
                if v == 'popularity':
                    return qs.order_by(Coalesce('reaction_count', 'comment_count').desc())
                if v == 'most_reactions':
                    return qs.order_by('-reaction_count')
                if v == 'most_comments':
                    return qs.order_by('-comment_count')
                if v == 'oldest':
                    return qs.order_by('created')
        return super().filter(qs, value)


class ConfessionFilter(FilterSet):
    sort_by = ConfessionOrderingFilter()

