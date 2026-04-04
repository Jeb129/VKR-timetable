# backend/api/views.py
import logging
import re
from typing import List
from rest_framework import viewsets, status
from rest_framework.views import Response
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from datetime import datetime
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from api.models import Classroom, Booking
from api.serializers import ClassroomSerializer, MappedEventSerializer
from api.services.schedule.mapper import (
    MappedEvent,
    get_classroom_schedule,
    get_group_schedule,
    get_teacher_schedule,
)
from api.serializers.requests import BookingSerializer

class ClassroomViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Classroom.objects.all().order_by("num")
    serializer_class = ClassroomSerializer
    permission_classes = [AllowAny]


# Вьюсет для бронирования (Создание заявок в BookingPage.tsx)
class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_class = [IsAuthenticated]

    # Фильтр заявок закрытых
    def get_queryset(self):
        queryset = Booking.objects.all()
        # Получаем статус из ссылки (?status=0)
        status_param = self.request.query_params.get("status")
        my_param = self.request.query_params.get("my")

        if status_param is not None:
            # Если параметр передан, фильтруем по нему
            queryset = queryset.filter(status=status_param)
        if my_param == "true":
            # Фильтруем по текущему пользователю из токена
            queryset = queryset.filter(user=self.request.user)
        return queryset.order_by("-created_at")
