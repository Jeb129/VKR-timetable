# backend/api/urls.py
from django.urls import path, include
from api.urls.database_set import router
from api.views.t_view import TestDraftScenarioView


urlpatterns = [
    path('', include(router.urls)),
    path("schedule/",include("api.urls.schedule")),
    path("scenario/<int:scenario_id>/",include("api.urls.scenario")),
    path("test/", TestDraftScenarioView.as_view())
]