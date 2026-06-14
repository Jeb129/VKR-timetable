from numpy import delete
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from api.models import Semester, PlannedLesson, AcademicLoad
from api.serializers import PlannedLessonSerializer, AcademicLoadSerializer
from api.services.schedule.planner import generate_planned_lessons_bulk
from authentification.permissions import IsScheduleModerator
from config.utils import SimpleRelatedSerializer


class PlannedLessonViewSet(viewsets.ModelViewSet):
    """
    Управление плановыми занятиями семестра.
    URL: /api/semester/{semester_id}/plannedlesson/
    """
    serializer_class = PlannedLessonSerializer
    permission_classes = [IsScheduleModerator]

    def get_queryset(self):
        # Фильтруем занятия только для текущего семестра
        return PlannedLesson.objects.filter(
            semester_id=self.kwargs['semester_id']
        ).prefetch_related('teachers', 'study_groups', 'discipline', 'lesson_type')

    @action(detail=False, methods=['post'])
    def generate(self, request, semester_id=None):
        """
        Автоматическое создание PlannedLesson на основе AcademicLoad.
        """
        clear_old_planned = request.query_params.get("force")
        try:
            semester = Semester.objects.get(pk=semester_id)
            if clear_old_planned:
                PlannedLesson.objects.filter(semester=semester).delete()
            loads = AcademicLoad.objects.filter(
                semester=semester,
                plannedlessons__isnull=True
            ).select_related(
                "discipline", "lesson_type", "study_group"
            )
            if not loads.exists():
                return Response(
                    {"message":f"В семестре {semester} не найдены нераспределенные записи учебной нагрузки"},
                    status = status.HTTP_404_NOT_FOUND
                )
            created_count = generate_planned_lessons_bulk(semester, loads)
        except Exception as err:
            return Response({
                "message":"При создании плановых занятий произошла ошибка",
                "error": str(err)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({
                "message": f"Успешно создано {created_count} плановых занятий",
                "count": created_count
            }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def check(self, request, semester_id=None):
        """
        Проверка покрытия нагрузки.
        Ищет записи AcademicLoad, для которых не создано ни одного PlannedLesson.
        """

        # Ищем нагрузку, у которой нет связанных PlannedLesson в этом семестре
        loads = AcademicLoad.objects.filter(
            semester_id=semester_id
        )
        if not loads.exists():
            return Response({
                "status": "warning",
                "message":"Не найдены записи учебной нагрузки для семестра"
            }, status = status.HTTP_404_NOT_FOUND)
        
        uncovered_load = loads.filter(
            plannedlessons__isnull=True
        ).distinct()
        if not uncovered_load.exists():
            return Response({
                "status": "ok",
                "message": "Вся учебная нагрузка распределена"
            }, status=status.HTTP_200_OK)

        # Если есть пропуски, возвращаем их список
        serializer = SimpleRelatedSerializer(uncovered_load, many=True)
        return Response({
            "status": "warning",
            "message": f"Найдено {uncovered_load.count()} нераспределенных записей учебной нагрузки",
            "uncovered_data": serializer.data
        }, status=status.HTTP_200_OK)
