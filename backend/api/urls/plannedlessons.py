from rest_framework.routers import DefaultRouter

from api.views import PlannedLessonViewSet

router = DefaultRouter()
router.register(r"plannedlessons",PlannedLessonViewSet,basename="plannedlessons")

urlpatterns = router.urls