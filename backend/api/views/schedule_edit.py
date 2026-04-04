from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from api.models.schedule import ScheduleScenario
from api.serializers import LessonSerializer
from api.services.constraunt.manager import ConstraintManager
from api.services.redis.storage import RedisDraftStorage
from api.services.schedule.draft.context import draft_context

class DraftScenarioView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, scenario_id: int):
        scenario = get_object_or_404(ScheduleScenario, id=scenario_id)
        storage = RedisDraftStorage(scenario_id, request.user.id)

        # Используем ConstraintManager и draft_context косвенно
        # (check_scenario_draft вызывает draft_context)
        with draft_context(scenario, storage) as dr_scenario:
            lessons = dr_scenario.lessons.all()
            serialized = LessonSerializer(lessons, many=True).data

        return Response({
            "scenario_id": scenario.id,
            "lessons": serialized,
            "has_draft": storage.has_any_changes(),
        })
    
class DraftLessonUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, scenario_id: int, lesson_id: int):
        scenario = get_object_or_404(ScheduleScenario, id=scenario_id)
        storage = RedisDraftStorage(scenario_id, request.user.id)

        # Готовый метод в ConstraintManager
        lesson, errors = ConstraintManager.prepare_draft_lesson(
            scenario=scenario,
            lesson_id=lesson_id,
            data=request.data,
            storage=storage
        )

        return Response({
            "lesson": LessonSerializer(lesson).data,
            "errors": [e.to_dict() for e in errors],
        })
    
class DraftLessonDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, scenario_id: int, lesson_id: int):
        scenario = get_object_or_404(ScheduleScenario, id=scenario_id)
        storage = RedisDraftStorage(scenario_id, request.user.id)

        storage.delete_lesson(lesson_id)

        return Response({"status": "ok"})

# class DraftScenarioCommitView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request, scenario_id: int):
#         scenario = get_object_or_404(ScheduleScenario, id=scenario_id)
#         storage = RedisDraftStorage(scenario_id, request.user.id)

#         # Применяем черновики к БД
#         commit_changes(scenario, storage)

#         # Чистим Redis
#         storage.clear_all()

#         return Response({"status": "committed"})