# backend/api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LessonViewSet, ClassroomViewSet # Проверьте названия ваших вьюсетов

router = DefaultRouter()
# Регистрируем пути:
router.register(r'lessons', LessonViewSet, basename='lesson')
router.register(r'classrooms', ClassroomViewSet, basename='classroom')

urlpatterns = [
    path('', include(router.urls)),
]