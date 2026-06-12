from django.urls import path

from authentification.views.auth import CookieTokenObtainPairView, CookieTokenRefreshView, CookieTokenVerifyView,LogoutView, RegisterView
from authentification.views.modelView import CurrentUserView,MoodleVerifyView, LinkGroupView

urlpatterns = [
    path("login/", CookieTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("register/", RegisterView.as_view(), name="register"),
    path("refresh/", CookieTokenRefreshView.as_view(), name="token_refresh"),
    path("verify/", CookieTokenVerifyView.as_view(), name="token_verify"),
    path("me/", CurrentUserView.as_view(), name="current_user"),
    path('moodle-verify/', MoodleVerifyView.as_view(), name='moodle_verify'),
    path('link-group/', LinkGroupView.as_view(), name='link_group'),
]
