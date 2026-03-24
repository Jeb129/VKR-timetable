# api/views.py
class LessonViewSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        scenario_id = self.request.query_params.get('scenario_id')
        classroom_id = self.request.query_params.get('classroom_id')
        return Lesson.objects.filter(scenario_id=scenario_id, classroom_id=classroom_id)