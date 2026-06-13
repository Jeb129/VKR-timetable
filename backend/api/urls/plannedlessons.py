from rest_framework.routers import DefaultRouter

from api.views import PlannedLessonViewSet

router = DefaultRouter()
router.register(r"lessons",PlannedLessonViewSet,basename="lessons")

urlpatterns = router.urls