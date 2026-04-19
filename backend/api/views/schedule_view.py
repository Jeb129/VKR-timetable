import logging
from typing import List
from rest_framework import status, viewsets
from rest_framework.views import Response
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from datetime import datetime
from rest_framework.permissions import AllowAny
from api.models import Timeslot, ScheduleScenario, Lesson
from api.serializers.schedule import ScheduleScenarioSerializer
from api.serializers import MappedEventSerializer, TimeslotSerializer
from api.services.schedule.mapper import (
    MappedEvent,
    get_classroom_schedule,
    get_group_schedule,
    get_teacher_schedule,
)

logger = logging.getLogger("cheker")


class TimeslotViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Timeslot.objects.all().order_by("day", "order_number")
    serializer_class = TimeslotSerializer
    permission_classes = [AllowAny]


class ScheduleScenarioViewSet(viewsets.ModelViewSet):
    queryset = ScheduleScenario.objects.all().order_by("-created_at")
    serializer_class = ScheduleScenarioSerializer
    permission_classes = [AllowAny]

    @action(detail=True, methods=['post'])
    def copy(self, request, pk=None):
        """
        метод для глубокого копирования сценария вместе с уроками
        URL: /api/scenarios/{id}/copy/
        """
        try:
            original_scenario = self.get_object()
            
            # Создаем новый объект сценария на основе старого
            new_scenario = ScheduleScenario.objects.create(
                name=f"{original_scenario.name} (Копия)",
                semester=original_scenario.semester,
                is_active=False # Копия всегда создается неактивной
            )

            # Получаем все уроки оригинала
            lessons = Lesson.objects.filter(scenario=original_scenario)
            
            for lesson in lessons:
                # Сохраняем связи ManyToMany перед обнулением PK
                teachers = list(lesson.teachers.all())
                groups = list(lesson.study_groups.all())

                # Клонируем объект урока
                lesson.pk = None 
                lesson.scenario = new_scenario
                lesson.save()

                # Восстанавливаем связи для нового объекта
                lesson.teachers.set(teachers)
                lesson.study_groups.set(groups)

            logger.info(f"Сценарий {original_scenario.id} успешно скопирован в {new_scenario.id}")
            
            serializer = self.get_serializer(new_scenario)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Ошибка при копировании сценария: {str(e)}")
            return Response({"error": "Не удалось скопировать сценарий"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ScheduleView(ListAPIView):
    serializer_class = MappedEventSerializer
    permission_classes = [AllowAny]

    def get_query_date(self):
        dt = self.request.query_params.get("date")
        dt_f = self.request.query_params.get("date_from")
        dt_t = self.request.query_params.get("date_to")
        if dt:
            return datetime.strptime(dt, "%Y-%m-%d"), datetime.strptime(dt, "%Y-%m-%d")

        if not dt_f:
            raise ValueError("Не передан параметр date_from")
        if not dt_t:
            raise ValueError("Не передан параметр date_to")

        return datetime.strptime(dt_f, "%Y-%m-%d"), datetime.strptime(dt_t, "%Y-%m-%d")

    def list(self, request, *args, **kwargs):
        try:
            logger.debug("запрос списка событий")
            data = self.get_queryset()
            serializer = self.get_serializer(data, many=True)
            return Response(serializer.data)
        except ValueError as e:
            logger.exception(e)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(e)
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GroupScheduleView(ScheduleView):
    def get_queryset(self) -> List[MappedEvent]:
        dt_f, dt_t = self.get_query_date()
        group_id = self.request.query_params.get("group_id")

        return get_group_schedule(date_from=dt_f, date_to=dt_t, group_id=group_id)


class ClassroomScheduleView(ScheduleView):
    def get_queryset(self) -> List[MappedEvent]:
        dt_f, dt_t = self.get_query_date()
        classroom_id = self.request.query_params.get("classroom_id")
        return get_classroom_schedule(
            classroom_id=int(classroom_id),
            date_from=dt_f,
            date_to=dt_t,
        )


class TeacherScheduleView(ScheduleView):
    def get_queryset(self) -> List[MappedEvent]:
        dt_f, dt_t = self.get_query_date()
        teacher_id = self.request.query_params.get("teacher_id")
        return get_teacher_schedule(date_from=dt_f, date_to=dt_t, teacher_id=teacher_id)
