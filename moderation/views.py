from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.db.models import Q, Count, Case, When, F

from . import models, serializers, permissions, filters


@extend_schema(responses=serializers.ReportSerializer)
class ReportViewSet(generics.ListCreateAPIView, generics.DestroyAPIView, viewsets.GenericViewSet):
    serializer_class = serializers.ReportSerializer
    queryset = models.Report.objects.all()
    permission_classes = (permissions.ReportPermission,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = filters.ReportFilter
    _vote_limit = 3

    @extend_schema(request=None)
    @action(methods=["post"], detail=True, url_path="vote", url_name="vote")
    def give_vote(self, request, *args, **kwargs):
        report = self.get_object()
        if report.voters.filter(pk=request.user.pk).exists():
            return Response({"error": "You already voted."}, status=status.HTTP_400_BAD_REQUEST)
        report.voters.add(request.user)
        if report.voters.count() == self._vote_limit:
            if report.confession:
                report.confession.delete()
            elif report.comment:
                report.comment.delete()
        serializer = self.get_serializer(report)
        return Response(serializer.data)


@extend_schema_view(list=extend_schema(parameters=None))
@extend_schema(
    parameters=[
        OpenApiParameter('handle', OpenApiTypes.STR, OpenApiParameter.PATH),
    ],
    responses=serializers.MessageSerializer
)
class MessageViewSet(generics.ListCreateAPIView, generics.RetrieveAPIView, viewsets.GenericViewSet):
    serializer_class = serializers.MessageSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = 'handle'
    _queryset_fields = ('handle',)  # , id

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._target_queryset_fields = tuple('target_' + field for field in self._queryset_fields)
        self._receiver_sender_queryset_fields = tuple(('receiver__' + field, 'sender__' + field) for field in self._queryset_fields)

    def get_queryset(self):
        queryset = models.Message.objects.filter(Q(sender=self.request.user) | Q(receiver=self.request.user))
        if self.action == 'list':
            annotate = {'target_' + self._queryset_fields[i]:
                        Case(When(Q(sender=self.request.user), then=F(self._receiver_sender_queryset_fields[i][0])),
                             When(Q(receiver=self.request.user), then=F(self._receiver_sender_queryset_fields[i][1])))
                        for i in range(len(self._queryset_fields))}
            queryset = queryset.annotate(**annotate).values(*self._target_queryset_fields)\
                .annotate(count=Count(self._target_queryset_fields[0])).values(*self._target_queryset_fields + ('count',))
        return queryset

    @extend_schema(responses=serializers.MessageListSerializer)
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = serializers.MessageListSerializer(queryset, many=True)
        return Response(serializer.data)

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        # if self.action != 'retrieve':
        #     obj = get_object_or_404(queryset, **{'pk': self.kwargs[lookup_url_kwarg]})
        #
        #     # May raise a permission denied
        #     self.check_object_permissions(self.request, obj)
        #
        #     return obj

        filter_args = Q()
        for f in ('sender', 'receiver'):
            filter_args |= Q(**{f + '__' + self.lookup_field: self.kwargs[lookup_url_kwarg]})
        return queryset.filter(filter_args)

    def retrieve(self, request, *args, **kwargs):
        queryset = self.get_object()

        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

