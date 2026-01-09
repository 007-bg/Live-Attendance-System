from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import ClassViewSet

router = DefaultRouter()
router.register(r"class", ClassViewSet, basename="class")

urlpatterns = router.urls
