from rest_fromwork.routers import DefaultRouter
from attendance_system.users.views import AuthViewSet

router = DefaultRouter()
router.register(r"auth", AuthViewSet, basename="auth")

urlpatterns = router.urls
