import logging
from datetime import datetime, time
from typing import List

from django.utils import timezone
from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import Response

from api.models import (Lesson, ScheduleScenario)
from api.pagination import StandartPagination
from api.serializers import (LessonReadSerializer,
                             MappedEventSerializer)
from api.serializers.database import ScheduleScenarioSerializer
from api.serializers.schedule import LessonErrorSerializer
from api.services.schedule.manager import ScheduleManager
from api.services.schedule.mapper import MappedEvent, ScheduleMapper
from authentification.permissions import IsScheduleModerator
from config.utils import normalize_diff

logger = logging.getLogger("cheker")

class DraftLessonViewSet(viewsets.ViewSet):
    """
    Контроллер для работы с черновыми Lesson.
    """
    permission_classes = [IsScheduleModerator]

    def list(self, request,scenario_id):
        """GET /draft/lessons/ — список черновиков"""

        group_id = request.query_params.get("group_id")
        teacher_id = request.query_params.get("teacher_id")
        classroom_id = request.query_params.get("classroom_id")
        with_errors = request.query_params.get("with_errors")
        
        manager = ScheduleManager(scenario_id=scenario_id,user=request.user).build_context(draft=True)
        lessons = None
        result = {}

        if group_id:
            lessons = manager.get_lessons_draft(study_groups__id=int(group_id))
        elif teacher_id:
            lessons = manager.get_lessons_draft(teachers__id=int(teacher_id))
        elif classroom_id:
            lessons = manager.get_lessons_draft(teachers__id=int(classroom_id))
        else:
            lessons=[]
        result["lessons"] = LessonReadSerializer(lessons, many=True).data

        if with_errors:
            errors = [manager.check_lesson(l) for l in lessons]
            result["errors"] = LessonErrorSerializer(errors,many=True).data
        
        return Response(result,status=status.HTTP_200_OK)


    def retrieve(self, request,scenario_id, pk=None):
        """GET /draft/lessons/<id>/?with_errors=True — один черновик"""
        with_errors = request.query_params.get("with_errors")
        manager = ScheduleManager(scenario_id=scenario_id,user=request.user).build_context(draft=True)

        lesson = manager.get_lessons_draft(id=pk)
        if with_errors:
            errors = manager.check_lesson(
                lesson=lesson,
            )
            return Response(LessonErrorSerializer(errors).data, status=status.HTTP_200_OK)
        else:
            return Response({
                "lesson": LessonReadSerializer(lesson).data
                },
                status=status.HTTP_200_OK
            )


    def create(self, request,scenario_id):
        """POST /draft/lessons/ — создать черновик"""
        data=normalize_diff(Lesson,request.data)
    
        manager = ScheduleManager(scenario_id=scenario_id,user=request.user)
        new_id = manager.create_lesson_draft(data=data)

        errors= manager.check_lesson_draft(
            lesson_id=new_id,
            build_context=True
        )
        return Response(LessonErrorSerializer(errors).data, status=status.HTTP_201_CREATED)


    def partial_update(self, request ,scenario_id, pk=None):
        """PATCH /draft/lessons/<id>/ — обновить черновик"""
        manager = ScheduleManager(scenario_id=scenario_id,user=request.user)
        manager.update_lesson_draft(
            lesson_id=int(pk),
            diff_data=normalize_diff(Lesson,request.data),
        )
        manager.build_context(draft=True)
        lessonError = manager.check_lesson_draft(lesson_id=int(pk))

        # Возможно в будущем будем проверять весь сценарий разом, чтобы не менять вывод на фронет, подгоняем ответ апи
        return Response(LessonErrorSerializer([lessonError], many = True).data,status=status.HTTP_200_OK)


    def destroy(self, request, scenario_id,pk=None):
        """DELETE /draft/lessons/<id>/ — удалить черновик"""
        ScheduleManager(scenario_id=scenario_id, user=request.user).delete_lessons_draft(lesson_id=pk)
        return Response(status=status.HTTP_200_OK)


    @action(detail=True, methods=["post"])
    def apply(self, request,scenario_id, pk=None):
        """POST /draft/lessons/apply - сохраняет Lesson в БД."""
        manager = ScheduleManager(scenario_id=scenario_id,user=request.user)

        lessonError = manager.check_scenario_draft()

        manager.apply_lessons(pk)
        return Response(LessonErrorSerializer(lessonError, many = True).data,status=status.HTTP_200_OK)
    
    @action(detail=True, methods=["get"])
    def check(self, request,scenario_id, pk=None):
        """GET /draft/lessons/check - Проверяет ошибки в сценарии"""
        manager = ScheduleManager(scenario_id=scenario_id,user=request.user)
        lessonError = manager.check_scenario_draft()
        return Response(LessonErrorSerializer(lessonError, many = True).data,status=status.HTTP_200_OK)

    @action(detail=False, methods=["patch"], url_path="bulk-patch")
    def bulk_patch(self, request, scenario_id):
        """
        PATCH /api/scenario/{id}/draft/lessons/bulk-patch/
        Payload: [{"id": "uuid-1", "timeslot": 10}, {"id": "uuid-2", "timeslot": 11}]
        """
        manager = ScheduleManager(scenario_id=scenario_id, user=request.user)
        data = request.data  # Это должен быть список объектов
        
        if not isinstance(data, list):
            return Response({"error": "Expected a list of updates"}, status=status.HTTP_400_BAD_REQUEST)

        results = []

        # 1. Сначала применяем ВСЕ изменения
        for item in data:
            lesson_id = item.get("id")
            # Убираем id из данных для обновления
            diff_data = {k: v for k, v in item.items() if k != "id"}
            
            manager.update_lesson_draft(
                lesson_id=lesson_id,
                diff_data=normalize_diff(Lesson, diff_data),
            )

        # 2. Теперь собираем ошибки для всех затронутых уроков
        # (В идеале в ScheduleManager должен быть метод для массовой проверки)
        manager.build_context(draft=True)
        for item in data:
            lesson_id = item.get("id")
            lesson_error = manager.check_lesson_draft(lesson_id=lesson_id)
            
            
            results.append(lesson_error)

        return Response(LessonErrorSerializer(results, many=True).data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=["get"], url_path="trash")
    def trash(self, request, scenario_id):
        """GET /api/scenario/{id}/draft/lessons/trash/ — список удаленных занятий"""
        manager = ScheduleManager(scenario_id=scenario_id, user=request.user)
        deleted_lessons = manager.get_deleted_lessons_draft()
        return Response(LessonReadSerializer(deleted_lessons, many=True).data)

    @action(detail=True, methods=["delete"])
    def clear(self,request,scenario_id,pk=None):
        lesson = ScheduleManager(scenario_id,request.user).clear_lessons(pk)
        return Response(LessonReadSerializer(lesson).data,status=status.HTTP_200_OK)
    
    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request, scenario_id):
        """
        GET /api/scenario/{id}/draft/lessons/summary/
        Один запрос для страницы подтверждения.
        """
        manager = ScheduleManager(scenario_id=scenario_id, user=request.user).build_context(draft=True)
        # 1. Получаем пары этого сценария из черновика (Redis + БД)
        all_lessons = manager.get_lessons_draft()
        # 2. Фильтруем только на измененые или новые
        changes = [ l for l in all_lessons  if hasattr(l, 'draft_originals') or hasattr(l, 'draft_created')  ]
        
        # 3. Получаем список удаленных (те, что в корзине)
        deleted = manager.get_deleted_lessons_draft()
        
        # 4. Запускаем проверку конфликтов по всему сценарию
        errors = manager.check_scenario_draft()
        # Оставляем только те LessonError, где список ошибок не пуст
        active_errors = [e for e in errors if e.errors]

        return Response({
            "changes": LessonReadSerializer(changes, many=True).data,
            "deleted": LessonReadSerializer(deleted, many=True).data,
            "errors": LessonErrorSerializer(active_errors, many=True).data,
            "has_changes": len(changes) > 0 or deleted.exists()
        }, status=status.HTTP_200_OK)


class ScheduleScenarioViewSet(viewsets.ModelViewSet):
    queryset = ScheduleScenario.objects.all().order_by("-created_at")
    serializer_class = ScheduleScenarioSerializer
    pagination_class = StandartPagination
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
        
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        force = request.query_params.get("force")

        current = self.get_object()
        activated = ScheduleScenario.objects.filter(
            semester = current.semester,
            is_active=True).exclude(id=current.id).first()
        
        with transaction.atomic():
            if activated is not None:
                if force:
                    activated.is_active = False
                    activated.save()
                else:
                    return Response({
                        "message": f"Cуществует активный вариант расписания для этого семестра: {activated}"
                    }, status = status.HTTP_403_FORBIDDEN)
            current.is_active = True
            current.save()

        serializer = self.get_serializer(current)
        return Response(serializer.data,status=status.HTTP_200_OK)
        
            
        


    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        pass
  

class ScheduleView(ListAPIView):
    serializer_class = MappedEventSerializer
    permission_classes = [AllowAny]

    def get_query_date(self):
        dt = self.request.query_params.get("date")
        dt_f = self.request.query_params.get("date_from")
        dt_t = self.request.query_params.get("date_to")
        
        if dt:
            # Парсим дату
            date_obj = datetime.strptime(dt, "%Y-%m-%d")
            # Начало дня (00:00:00)
            start = timezone.make_aware(datetime.combine(date_obj, time.min))
            # Конец дня (23:59:59), чтобы захватить все события за этот день
            end = timezone.make_aware(datetime.combine(date_obj, time.max))
            return start, end

        if not dt_f or not dt_t:
            raise ValueError("Не переданы параметры date_from / date_to")

        # Парсим границы диапазона
        df_obj = datetime.strptime(dt_f, "%Y-%m-%d")
        dt_obj = datetime.strptime(dt_t, "%Y-%m-%d")

        # Делаем их "осознанными" и устанавливаем время на начало и конец дня соответственно
        start = timezone.make_aware(datetime.combine(df_obj, time.min))
        end = timezone.make_aware(datetime.combine(dt_obj, time.max))

        return start, end

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
        return ScheduleMapper(
            date_from=dt_f,
            date_to=dt_t,
            group_id=int(group_id)
        ).get_schedule()


class ClassroomScheduleView(ScheduleView):
    def get_queryset(self) -> List[MappedEvent]:
        dt_f, dt_t = self.get_query_date()
        if dt_f == dt_t:
            dt_t = datetime.combine(dt_t.date(),time.max)

        classroom_id = self.request.query_params.get("classroom_id")
        return ScheduleMapper(
            date_from=dt_f,
            date_to=dt_t,
            classroom_id=int(classroom_id)
        ).get_schedule()


class TeacherScheduleView(ScheduleView):
    def get_queryset(self) -> List[MappedEvent]:
        dt_f, dt_t = self.get_query_date()
        teacher_id = self.request.query_params.get("teacher_id")
        return ScheduleMapper(
            date_from=dt_f,
            date_to=dt_t,
            teacher_id=int(teacher_id)
        ).get_schedule()
