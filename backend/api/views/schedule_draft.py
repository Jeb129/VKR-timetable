from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.request import Request

from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from api.models import Lesson
from api.serializers import LessonReadSerializer
from api.serializers.education import LessonSerializer
from api.serializers.schedule import LessonErrorSerializer
from api.services.schedule.manager import ScheduleManager

from config.utils import normalize_diff

class DraftLessonViewSet(viewsets.ViewSet):
    """
    Контроллер для работы с черновыми Lesson.
    """
    permission_classes = [IsAuthenticated]

    def list(self, request,scenario_id):
        """GET /draft/lessons/ — список черновиков"""

        group_id = request.query_params.get("group_id")
        teacher_id = request.query_params.get("teacher_id")
        with_errors = request.query_params.get("with_errors")
        
        manager = ScheduleManager(scenario_id=scenario_id,user=request.user).build_context(draft=True)
        lessons = None

        if group_id:
            lessons = manager.get_lessons_draft(study_groups__id=int(group_id))
        elif teacher_id:
            lessons = manager.get_lessons_draft(teachers__id=int(teacher_id))

        if with_errors:
            errors = [manager.check_lesson(l) for l in lessons]
            return Response({
                "lessons":LessonReadSerializer(lessons, many=True).data,
                "errors":LessonErrorSerializer(errors,many=True).data
            },
                status=status.HTTP_200_OK
            )
            

        return Response(
                LessonReadSerializer(lessons, many=True).data,
                status=status.HTTP_200_OK
            )


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
            return Response(LessonReadSerializer(lesson).data,status=status.HTTP_200_OK)


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
        lessonError = ScheduleManager(scenario_id=scenario_id,user=request.user).update_lesson_draft(
            lesson_id=int(pk),
            diff_data=normalize_diff(Lesson,request.data),
        )

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

        manager.apply_lessons()
        return Response(LessonErrorSerializer(lessonError, many = True).data,status=status.HTTP_200_OK)
    
    @action(detail=True, methods=["get"])
    def check(self, request,scenario_id, pk=None):
        """GET /draft/lessons/check - Проверяет ошибки в сценарии"""
        manager = ScheduleManager(scenario_id=scenario_id,user=request.user)
        lessonError = manager.check_scenario_draft()
        return Response(LessonErrorSerializer(lessonError, many = True).data,status=status.HTTP_200_OK)


