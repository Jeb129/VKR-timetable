from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from django.db.models import Value, F, CharField
from django.db.models.functions import Concat
from api.models import Semester, PlannedLesson, AcademicLoad
from api.serializers import PlannedLessonSerializer
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
            semester_id=semester_id,
        )
        if not loads.exists():
            return Response({
                "status": "warning",
                "message":"Не найдены записи учебной нагрузки для семестра"
            }, status = status.HTTP_404_NOT_FOUND)

        uncovered_qs = loads.filter(plannedlessons__isnull=False)
        uncovered_count = uncovered_qs.count()
        if uncovered_count == 0:
            return Response({
                "status": "ok",
                "message": "Вся учебная нагрузка распределена"
            }, status=status.HTTP_200_OK)
        
        uncovered_load = uncovered_qs.annotate(
            name=Concat(
                F("teacher__name"), Value(", "),
                F("study_group__name"), Value(" - "),
                F('lesson_type__short_name'), Value(" "), F('discipline__name'),
                output_field=CharField()
            )
        ).select_related(
            "discipline", "lesson_type", "study_group","teacher"
        ).values('id', 'name')

        # Если есть пропуски, возвращаем их список
        return Response({
            "status": "warning",
            "message": f"Найдено {uncovered_count} нераспределенных записей учебной нагрузки",
            "uncovered_data": list(uncovered_load)
        }, status=status.HTTP_200_OK)
