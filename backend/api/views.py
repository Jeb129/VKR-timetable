# backend/api/views.py
import logging
from typing import List
from rest_framework import viewsets, status
from rest_framework.views import APIView, Response
from rest_framework.generics import ListAPIView, GenericAPIView
from rest_framework.response import Response
from datetime import datetime
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from api.models import Lesson, Classroom, Booking
from django.utils.dateparse import parse_date
from api.serializers import ClassroomSerializer, MappedEventSerializer
from api.services.schedule.mapper import MappedEvent, get_classroom_schedule, get_group_schedule, get_teacher_schedule
from .serializers.requests import BookingSerializer

logger = logging.getLogger("cheker")

class ClassroomViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Classroom.objects.all().order_by("num")
    serializer_class = ClassroomSerializer   
    permission_classes = [AllowAny]

class GroupScheduleView(ListAPIView):
    serializer_class = MappedEventSerializer
    permission_classes = [AllowAny]

    def get_queryset(self) -> List[MappedEvent]:
        dt_f = self.request.query_params.get("date_from")
        dt_t = self.request.query_params.get("date_to")
        group_id = self.request.query_params.get("group_id")
        return get_group_schedule(
            date_from=dt_f,
            date_to=dt_t,
            group_id=group_id
        )
    
    def list(self, request, *args, **kwargs):
        data = self.get_queryset()
        serializer = self.get_serializer(data, many=True)
        return Response(serializer.data)

class ClassroomScheduleView(ListAPIView):
    serializer_class = MappedEventSerializer

    def list(self, request, *args, **kwargs):
        # Получаем параметры из запроса
        date_str = request.query_params.get("date") or request.query_params.get("date_from")
        classroom_id = request.query_params.get("classroom_id")

        if not date_str or not classroom_id:
            return Response({"error": "Параметры date и classroom_id обязательны"}, status=400)

        try:
            # Превращаем строку "2026-03-30" в объект datetime для маппера
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            
            # Вызываем маппер (он сам разберется с числителем/знаменателем)
            mapped_events = get_classroom_schedule(
                classroom_id=int(classroom_id),
                date_from=dt,
                date_to=dt
            )
            
            # Логируем количество найденных событий (исправленная версия того, что не работало)
            logger.debug(f"Найдено событий для аудитории {classroom_id}: {len(mapped_events)}")
            
            serializer = self.get_serializer(mapped_events, many=True)
            return Response(serializer.data)
        
        except ValueError as e:
            return Response({"error": f"Неверный формат даты: {e}"}, status=400)
        except Exception as e:
            logger.error(f"Ошибка маппера: {e}")
            return Response({"error": "Ошибка при формировании расписания"}, status=500)
    
class TeacherScheduleView(ListAPIView):
    serializer_class = MappedEventSerializer

    def get_queryset(self) -> List[MappedEvent]:
        dt_f = self.request.query_params.get("date_from")
        dt_t = self.request.query_params.get("date_to")
        teacher_id = self.request.query_params.get("teacher_id")
        return get_teacher_schedule(
            date_from=dt_f,
            date_to=dt_t,
            teacher_id=teacher_id
        )
    
    def list(self, request, *args, **kwargs):
        data = self.get_queryset()
        serializer = self.get_serializer(data, many=True)
        return Response(serializer.data)

# Вьюсет для бронирования (Создание заявок в BookingPage.tsx)
class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_class = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def busy_slots(self, request):
        """
        Метод для FullCalendar, чтобы показать занятые места.
        В идеале здесь тоже стоит вызвать маппер, чтобы видеть уроки.
        """
        room_id = request.query_params.get('classroom_id')
        date_str = request.query_params.get('date')
        
        if not room_id or not date_str:
            return Response([])

        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        # Используем маппер, чтобы получить ВСЕ события (уроки и брони)
        data = get_classroom_schedule(
            date_from=date_obj,
            date_to=date_obj,
            classroom_id=int(room_id)
        )
        
        # Упрощаем формат для фронтенда (FullCalendar)
        busy = []
        for item in data:
            busy.append({
                "start": item.date_start.strftime("%H:%M"),
                "end": item.date_end.strftime("%H:%M"),
                "title": item.type, 
                "type": item.type
            })
        return Response(busy)
