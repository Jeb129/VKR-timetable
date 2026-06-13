from rest_framework.routers import DefaultRouter

from api.views import GenerationViewSet

router = DefaultRouter()
router.register(r"lessons",GenerationViewSet)

urlpatterns = router.urls