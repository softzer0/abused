from django.utils import timezone
from django.contrib.auth import login
from django.db.models import Q, Count, Case, When
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from rest_framework import generics, viewsets, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter

from djangoProject.common import is_string_truthy, get_current_session, IsAdminOrReadOnly, DefaultCursorPagination
from member.models import User
from . import serializers, permissions, models, filters


@extend_schema(responses=serializers.CategorySerializer)
class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.CategorySerializer
    permission_classes = (IsAdminOrReadOnly,)
    queryset = models.Category.objects.all()


OWN_QUERY_PARAM_DEFINITION = dict(list=extend_schema(
    parameters=[
        OpenApiParameter('own', OpenApiTypes.BOOL, OpenApiParameter.QUERY),
    ]
))
@extend_schema_view(**OWN_QUERY_PARAM_DEFINITION)
@extend_schema(responses=serializers.ConfessionSerializer)
class ConfessionViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.ConfessionSerializer
    permission_classes = (permissions.ConfessionPermission,)
    queryset = models.Confession.objects.all().annotate(comment_count=Count('comment'), reaction_count=Count('reaction')).order_by('-pk')
    filter_backends = (DjangoFilterBackend, SearchFilter)
    search_fields = ('title', 'text', 'tags__name', 'categories__name')
    filterset_class = filters.ConfessionFilter

    def get_queryset(self):
        if self.request.user.is_authenticated:
            if is_string_truthy(self.request.query_params.get('own', False)):
                self.queryset = self.queryset.filter(author=self.request.user)
            if self.request.user.role not in ['admin', 'moderator']:
                self.queryset = self.queryset.filter(Q(author=self.request.user) | Q(is_approved=True)).order_by('is_approved')
        else:
            self.queryset = self.queryset.filter(is_approved=True)
        return self.queryset

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            user = User.objects.create()
            login(self.request, User.objects.create(last_login=timezone.now()))
            session = get_current_session(self.request)
            session.user = user
            session.save()
        elif models.Confession.objects.filter(author=self.request.user, created__gte=timezone.now() - timezone.timedelta(days=1)).exists():
            return Response({"error": "You already made one confession in the last day."}, status=status.HTTP_403_FORBIDDEN)
        serializer.save()


class BaseCommentReactionView(generics.GenericAPIView):
    filter_backends = [DjangoFilterBackend]

    def check_is_own(self):
        if 'is_own' in self.kwargs:
            return True
        if self.request.user.is_authenticated and is_string_truthy(self.request.query_params.get('own', False)):
            self.kwargs['is_own'] = None
            return True

    def get_queryset(self):
        if self.check_is_own():
            return self.queryset.filter(sender=get_current_session(self.request))
        return self.queryset


@extend_schema_view(**OWN_QUERY_PARAM_DEFINITION)
@extend_schema(responses=serializers.CommentSerializer)
class CommentViewSet(BaseCommentReactionView, generics.ListCreateAPIView, generics.RetrieveDestroyAPIView, viewsets.GenericViewSet):
    serializer_class = serializers.CommentSerializer
    permission_classes = (permissions.CommentReactionPermission,)
    pagination_class = DefaultCursorPagination
    queryset = models.Comment.objects.all()
    filterset_fields = ('confession',)

    def perform_create(self, serializer):
        if models.Comment.objects.filter(sender=get_current_session(self.request), created__gte=timezone.now() - timezone.timedelta(hours=1)).count() == 3:
            return Response({"error": "You already gave three comments in the last hour."}, status=status.HTTP_403_FORBIDDEN)
        serializer.save()


@extend_schema_view(**OWN_QUERY_PARAM_DEFINITION)
@extend_schema(responses=serializers.ReactionSerializer)
class ReactionViewSet(BaseCommentReactionView, generics.ListCreateAPIView, generics.RetrieveDestroyAPIView, viewsets.GenericViewSet):
    serializer_class = serializers.ReactionSerializer
    permission_classes = (permissions.CommentReactionPermission,)
    queryset = models.Reaction.objects.all()
    filterset_fields = ('confession', 'comment')

    def list(self, request, *args, **kwargs):
        if self.check_is_own():
            return super().list(request, *args, **kwargs)
        if not request.query_params.get('confession', None) and not request.query_params.get('comment', None):
            return Response({"error": "You must specify either of the filters in query."}, status=status.HTTP_400_BAD_REQUEST)
        queryset = self.filter_queryset(self.get_queryset())
        extra_annotate = {}
        if request.user.is_authenticated:
            extra_annotate['is_author'] = Case(When(sender=get_current_session(request), then=True), default=False)
        return Response({"results": queryset.values('emoji').annotate(count=Count('emoji'), **extra_annotate)})

    def perform_create(self, serializer):
        if models.Reaction.objects.filter(sender=get_current_session(self.request), created__gte=timezone.now() - timezone.timedelta(hours=1)).count() == 3:
            return Response({"error": "You already gave three reactions in the last hour."}, status=status.HTTP_403_FORBIDDEN)
        serializer.save()

