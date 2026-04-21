from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from authentification.views import CurrentUserView, LogoutView, RegisterView,MoodleVerifyView, MockMoodleAPIView

urlpatterns = [
    path("login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("register/", RegisterView.as_view(), name="register"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("me/", CurrentUserView.as_view(), name="current_user"),
    path('moodle-verify/', MoodleVerifyView.as_view(), name='moodle_verify'),
    path('mock-moodle/', MockMoodleAPIView.as_view()), # заглушка на тест
]
