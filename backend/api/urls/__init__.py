# backend/api/urls.py
from django.urls import path, include
from api.urls.infrastructure import router
from api.views.test_view import TestDraftScenarioView


urlpatterns = [
    path('', include(router.urls)),
    path('', include('api.urls.infrastructure')), 
    path("schedule/",include("api.urls.schedule")),
    path("scenario/<int:scenario_id>/",include("api.urls.scenario")),
    path("test/", TestDraftScenarioView.as_view())
]