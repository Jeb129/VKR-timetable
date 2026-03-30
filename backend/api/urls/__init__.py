# backend/api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views import ClassroomViewSet # Проверьте названия ваших вьюсетов

router = DefaultRouter()
# Регистрируем пути:
router.register(r'classrooms', ClassroomViewSet, basename='classroom')

urlpatterns = [
    path('', include(router.urls)),
    path("schedule/",include("api.urls.schedule"))
]