from django.urls import path
from rest_framework import routers

from . import views

urlpatterns = [
    path('user/logout', views.UserViewSet.as_view({'get': 'logout'})),
    path('user/', views.UserViewSet.as_view({'get': 'list'})),
    path('user/me', views.UserViewSet.as_view({
        'get': 'retrieve',
        'post': 'authenticate',
        'put': 'update',
        'patch': 'partial_update'
    })),
]

router = routers.DefaultRouter()
router.register(r'blocklist', views.BlocklistViewSet, basename='blocklist')

urlpatterns += router.urls

