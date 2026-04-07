from django.urls import path

from api.views import DraftScenarioView, DraftScenarioCommitView

urlpatterns =[
    path("draft/",DraftScenarioView.as_view(), name="draft"),
    path("draft/commit/",DraftScenarioCommitView.as_view(), name="draft"),
]