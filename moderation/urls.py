from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'report', views.ReportViewSet, basename='report')
router.register(r'message', views.MessageViewSet, basename='message')

urlpatterns = router.urls
