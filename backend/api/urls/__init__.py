from django.urls import path, include
from api.views.t_view import TestDraftScenarioView
from api.views.excel import ExcelAPIView
from api.views.statistics import BuildingLoadView


urlpatterns = [
    path('', include("api.urls.database")),
    path("schedule/",include("api.urls.schedule")),
    path("scenario/<int:scenario_id>/draft/",include("api.urls.draftlessons")),
    path("semester/<int:semester_id>/",include("api.urls.plannedlessons")),
    path('academic-load/import/', ExcelAPIView.as_view(), name='excel-import-api'),
    path("test/", TestDraftScenarioView.as_view()),
    path('statistics/load/', BuildingLoadView.as_view(), name='stats-load'),
]