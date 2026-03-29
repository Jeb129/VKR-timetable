# backend/api/views.py
from typing import List

from django.db.models.manager import BaseManager
from rest_framework import viewsets, status
from rest_framework.views import APIView, Response
from rest_framework.generics import ListAPIView, GenericAPIView
from datetime import datetime
from api.models import Lesson, Classroom
from api.serializers import LessonSerializer,ClassroomSerializer, MappedEventSerializer
from api.services.schedule.mapper import MappedEvent, get_classroom_schedule, get_group_schedule, get_teacher_schedule


class LessonViewSet(APIView):
    # УДАЛИТЬ НАХУЙ ПРИ ПЕРВОЙ ВОЗМОЖНОСТИ
    # Все представления для получения расписания переехали ниже
    def get(self, request) -> Response:
        return Response({"message":"Представления поменялись, раз наткнулся - переделывай"},status=status.HTTP_301_MOVED_PERMANENTLY)

class ClassroomViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Classroom.objects.all().order_by("num")
    serializer_class = ClassroomSerializer

class GroupScheduleView(ListAPIView):
    serializer_class = MappedEventSerializer

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

    def get_queryset(self) -> List[MappedEvent]:
        dt_f = self.request.query_params.get("date_from")
        dt_t = self.request.query_params.get("date_to")
        classroom_id = self.request.query_params.get("classroom_id")
        return get_classroom_schedule(
            date_from=dt_f,
            date_to=dt_t,
            classroom_id=classroom_id
        )
    
    def list(self, request, *args, **kwargs):
        data = self.get_queryset()
        serializer = self.get_serializer(data, many=True)
        return Response(serializer.data)
    
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
