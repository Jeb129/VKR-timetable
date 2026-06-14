from rest_framework.routers import DefaultRouter

from api.views import DraftLessonViewSet

router = DefaultRouter()
router.register(r"lessons",DraftLessonViewSet,basename="lessons")

urlpatterns = router.urls