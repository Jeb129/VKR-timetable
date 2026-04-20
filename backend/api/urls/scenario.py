from django.urls import path,include
from rest_framework.routers import DefaultRouter

from api.views import DraftLessonViewSet

router = DefaultRouter()
router.register(r"lessons",DraftLessonViewSet,basename="lessons")

urlpatterns =[
    # path("draft/",DraftScenarioView.as_view(), name="draft"),
    path("draft/",include(router.urls), name="draft"),
]