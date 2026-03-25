# api/views.py
class LessonViewSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        scenario_id = self.request.query_params.get('scenario_id')
        classroom_id = self.request.query_params.get('classroom_id')
        return Lesson.objects.filter(scenario_id=scenario_id, classroom_id=classroom_id)

class LessonViewSet(viewsets.ModelViewSet):
    serializer_class = LessonSerializer

    def get_queryset(self):
        queryset = Lesson.objects.all().select_related(
            'discipline', 'lesson_type', 'timeslot', 'classroom'
        ).prefetch_related('teachers', 'study_groups')

        # Фильтр по аудитории
        classroom_id = self.request.query_params.get('classroom_id')
        if classroom_id:
            queryset = queryset.filter(classroom_id=classroom_id)

        # По умолчанию берем только активный сценарий (EIOS Import или твой)
        queryset = queryset.filter(scenario__is_active=True)

        return queryset.order_by('timeslot__order_number')