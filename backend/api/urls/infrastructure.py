from rest_framework.routers import DefaultRouter
from api.views import ClassroomViewSet, BookingViewSet

router = DefaultRouter()
router.register(r'classrooms', ClassroomViewSet, basename='classroom')
router.register(r'bookings', BookingViewSet, basename='booking')

urlpatterns = router.urls