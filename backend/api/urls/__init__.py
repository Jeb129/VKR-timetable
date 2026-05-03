# backend/api/urls.py
from django.urls import path, include
from api.urls.database_set import router
from api.views.t_view import TestDraftScenarioView
from api.views.academic_load import ExcelAPIView
from api.views.statistics import BuildingLoadView


urlpatterns = [
    path('', include(router.urls)),
    path("schedule/",include("api.urls.schedule")),
    path("scenario/<int:scenario_id>/",include("api.urls.scenario")),
    path('academic-load/import/', ExcelAPIView.as_view(), name='excel-import-api'),
    path("test/", TestDraftScenarioView.as_view()),
    path('statistics/load/', BuildingLoadView.as_view(), name='stats-load'),
]