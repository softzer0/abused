from django.contrib.auth import login, logout
from drf_spectacular.types import OpenApiTypes
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter
from rest_framework import generics, viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action, permission_classes as permission_classes_decorator

from djangoProject.common import PermissionsPerMethodMixin, IsAdmin
from member import models
from . import serializers


@extend_schema_view(
    list=extend_schema(parameters=[OpenApiParameter(
        name='ordering',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        enum=['created', '-created']
    )]),
    logout=extend_schema(responses=None)
)
@extend_schema(responses=serializers.UserSerializer)
class UserViewSet(PermissionsPerMethodMixin, generics.ListAPIView, generics.RetrieveUpdateDestroyAPIView, viewsets.GenericViewSet):
    serializer_class = serializers.UserSerializer
    queryset = models.User.objects.all()
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = ('role',)
    ordering_fields = ('created',)

    def get_object(self):
        return self.request.user

    @action(methods=['POST'], detail=False)
    @permission_classes_decorator((permissions.AllowAny,))
    def authenticate(self, request):
        if request.user.is_authenticated:
            return Response({"error": "Already authenticated, please logout first"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = serializers.UserSerializer(data=request.data, is_auth=True)
        serializer.is_valid(raise_exception=True)
        user = models.User.objects.get(handle=serializer.validated_data['handle'])
        if not user.is_password_custom and user.password != serializer.validated_data['password'] or \
                user.is_password_custom and not user.check_password(serializer.validated_data['password']):
            return Response({"error": "Invalid password"}, status=status.HTTP_400_BAD_REQUEST)
        login(request, user)
        serializer.validated_data['password'] = user.password
        return Response(serializer.data)

    @action(methods=['GET'], detail=False)
    @permission_classes_decorator((permissions.IsAuthenticated,))
    def logout(self, request):
        logout(request)
        return Response({"message": "Logged out"})

    @permission_classes_decorator((IsAdmin,))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


@extend_schema_view(
    list=extend_schema(parameters=[OpenApiParameter(
        name='ordering',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        enum=['pk', '-pk', 'expires', '-expires']
    )])
)
@extend_schema(responses=serializers.BlocklistSerializer)
class BlocklistViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.BlocklistSerializer
    permission_classes = (IsAdmin,)
    queryset = models.Blocklist.objects.all()
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = ('session__ip_address',)
    ordering_fields = ('pk', 'expires')

