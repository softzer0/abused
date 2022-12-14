# from django.urls import path
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'category', views.CategoryViewSet, basename='category')
router.register(r'entry', views.ConfessionViewSet, basename='entry')
router.register(r'comment', views.CommentViewSet, basename='comment')
router.register(r'reaction', views.ReactionViewSet, basename='reaction')

urlpatterns = router.urls
