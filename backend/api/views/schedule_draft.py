from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from api.models import Lesson
from api.serializers import LessonSerializer
from api.serializers.schedule import ConstraintErrorSerializer
from api.services.constraunt.manager import ScheduleManager

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

        manager = ScheduleManager(scenario_id=scenario_id,user=request.user)
        lessons = None
        if group_id:
            lessons = manager.get_lessons_draft(study_groups__id=int(group_id))
        elif teacher_id:
            lessons = manager.get_lessons_draft(teachers__id=int(teacher_id))

        return Response({
            "lessons": LessonSerializer(lessons, many=True).data,
            "has_draft": manager.has_draft(),
        },status=status.HTTP_200_OK)


    def retrieve(self, request,scenario_id, pk=None):
        """GET /draft/lessons/<id>/?with_errors=True — один черновик"""
        with_errors = request.query_params.get("with_errors")
        manager = ScheduleManager(scenario_id=scenario_id,user=request.user)

        lesson = manager.get_lessons_draft(id=pk).first()
        if with_errors:
            errors = manager.init_constraints().update_lesson_draft(
                lesson_id=pk,
                data=normalize_diff(Lesson,request.data),
            )
            return Response(
                {
                    "lesson":LessonSerializer(lesson).data,
                    "errors":ConstraintErrorSerializer(errors, many=True).data
                }, status=status.HTTP_200_OK
            )
        else:
            return Response(LessonSerializer(lesson).data,status=status.HTTP_200_OK)


    def create(self, request,scenario_id):
        """POST /draft/lessons/ — создать черновик"""
        manager = ScheduleManager(scenario_id=scenario_id,user=request.user)
        new_id = manager.create_lesson_draft(data=normalize_diff(Lesson,request.data))

        errors= manager.init_constraints().check_lesson_draft(
            lesson_id=new_id,
        )
        return Response({
            "id": new_id,
            "errors": ConstraintErrorSerializer(errors, many=True),
        },status=status.HTTP_201_CREATED)


    def partial_update(self, request,scenario_id, pk=None):
        """PATCH /draft/lessons/<id>/ — обновить черновик"""
        # Готовый метод в commit_scenario
        errors = ScheduleManager(scenario_id=scenario_id,user=request.user).init_constraints().update_lesson_draft(
            lesson_id=pk,
            data=normalize_diff(Lesson,request.data),
        )
 
        #фильтрация ошибок с 0 штрафом
        real_errors = [e for e in errors if e.penalty > 0]
        return Response({
            # "errors": len(errors),
            "errors": ConstraintErrorSerializer(real_errors, many = True).data,
        })


    def destroy(self, request, scenario_id,pk=None):
        """DELETE /draft/lessons/<id>/ — удалить черновик"""
        ScheduleManager(scenario_id=scenario_id, user=request.user).delete_lessons_draft(lesson_id=pk)
        return Response(status=status.HTTP_200_OK)


    @action(detail=True, methods=["post"])
    def apply(self, request,scenario_id, pk=None):
        """POST /draft/lessons/apply - сохраняет Lesson в БД."""
        manager = ScheduleManager(scenario_id=scenario_id,user=request.user)

        errors = manager.init_constraints().check_scenario_draft()
        real_errors = [e for e in errors if e.penalty > 0]
        manager.apply_lessons()
        return Response({
            # "errors": len(errors),
            "errors": ConstraintErrorSerializer(real_errors, many = True).data,
        })
