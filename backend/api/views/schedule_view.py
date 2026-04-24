import logging
from typing import List
from rest_framework import status, viewsets
from rest_framework.views import Response, APIView
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from datetime import datetime
from rest_framework.permissions import AllowAny,IsAuthenticated
from api.models import Timeslot, ScheduleScenario, Lesson, ScheduleAdjustment
from api.serializers.schedule import ScheduleScenarioSerializer
from api.serializers import MappedEventSerializer, TimeslotSerializer,ScheduleAdjustmentSerializer
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

class MyTeacherScheduleView(ScheduleView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> List[MappedEvent]:
        dt_f, dt_t = self.get_query_date()
        # Берем пользователя из запроса (его определил JWT middleware)
        user = self.request.user
        # Находим связанного преподавателя через OneToOneField
        try:
            teacher = user.teacher
        except Exception:
            raise ValueError("Ваш аккаунт не связан с профилем преподавателя")
        # Вызываем маппер, используя ID найденного преподавателя
        return get_teacher_schedule(
            date_from=dt_f,
            date_to=dt_t,
            teacher_id=teacher.id
        )


class ScheduleAdjustmentCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        lesson_id = request.data.get("lesson_id")
        target_date_str = request.data.get("date")
        target_timeslot_id = request.data.get("timeslot_id")
        description = request.data.get("description", "Перенос по согласованию")

        # Проверка данных
        lesson = Lesson.objects.get(id=lesson_id)
        timeslot = Timeslot.objects.get(id=target_timeslot_id)
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()

        # Создаем заявку на перенос
        adjustment = ScheduleAdjustment.objects.create(
            user=request.user,
            lesson=lesson,
            date=target_date,
            timeslot=timeslot,
            description=description,
            status=0 # ON_MODERATION
        )

        return Response({"message": "Заявка на перенос отправлена модератору"}, status=201)

class ScheduleAdjustmentViewSet(viewsets.ModelViewSet):
    queryset = ScheduleAdjustment.objects.all().order_by("-created_at")
    serializer_class = ScheduleAdjustmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        # Добавляем фильтрацию по статусу (?status=0)
        status_param = self.request.query_params.get("status")
        if status_param is not None:
            queryset = queryset.filter(status=status_param)
        return queryset
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Метод одобрения переноса пары"""
        obj = self.get_object()
        obj.status = 1  # VERIFIED
        obj.save()
        return Response({'status': 'verified'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Метод отклонения переноса пары"""
        obj = self.get_object()
        comment = request.data.get("admin_comment")
        if not comment:
            return Response({"detail": "Причина отказа обязательна"}, status=status.HTTP_400_BAD_REQUEST)
        
        obj.status = 2  # REJECTED
        obj.admin_comment = comment
        obj.save()
        return Response({'status': 'rejected'}, status=status.HTTP_200_OK)