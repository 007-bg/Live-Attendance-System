from rest_framework.routers import DefaultRouter
from users.views import AuthViewSet, StudentViewSet

router = DefaultRouter()
router.register(r"auth", AuthViewSet, basename="auth")
router.register(r"students", StudentViewSet, basename="students")

urlpatterns = router.urls
