from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from api.models import Semester, PlannedLesson, AcademicLoad
from api.serializers import PlannedLessonSerializer, AcademicLoadSerializer
from api.services.schedule.planner import generate_planned_lessons_bulk
from authentification.permissions import IsScheduleModerator


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
        Удаляет старые плановые занятия семестра!
        """
        try:
            semester = Semester.objects.get(pk=semester_id)
            loads = AcademicLoad.objects.filter(semester = semester)
            created_count = generate_planned_lessons_bulk(semester,loads)
        except Exception as err:
            return Response({"error": str(err)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
        uncovered_load = AcademicLoad.objects.filter(
            semester_id=semester_id,
            plannedlesson__isnull=True
        ).distinct()

        if not uncovered_load.exists():
            return Response({
                "status": "ok",
                "message": "All academic load is covered by planned lessons."
            })

        # Если есть пропуски, возвращаем их список
        serializer = AcademicLoadSerializer(uncovered_load, many=True)
        return Response({
            "status": "warning",
            "message": f"Found {uncovered_load.count()} uncovered load records",
            "uncovered_data": serializer.data
        }, status=status.HTTP_200_OK)