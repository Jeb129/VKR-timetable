from email import errors

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from api.models.schedule import Lesson, ScheduleScenario
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
        with draft_context(scenario, storage):
            lessons = Lesson.objects.all()
            serialized = LessonSerializer(lessons, many=True).data

        return Response({
            "lessons": serialized,
            "has_draft": storage.has_any_changes(),
        },status=status.HTTP_200_OK)
    
    def put(self, request, scenario_id: int):
        lesson_id = self.request.query_params.get("lesson_id")
        scenario = get_object_or_404(ScheduleScenario, id=scenario_id)
        storage = RedisDraftStorage(scenario_id, request.user.id)

        # Готовый метод в ConstraintManager
        errors= ConstraintManager().load().prepare_draft_lesson(
            scenario=scenario,
            lesson_id=lesson_id,
            data=request.data,
            storage=storage
        )

        return Response({
            "errors": [e for e in errors],
        })
    def delete(self, request, scenario_id: int):
        storage = RedisDraftStorage(scenario_id, request.user.id)

        lesson_id = self.request.query_params.get("lesson_id")
        if lesson_id:
            storage.delete_lesson(lesson_id)
        else:
            storage.clear_all()

        return Response(status=status.HTTP_200_OK)


class DraftScenarioCommitView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, scenario_id: int):
        # storage = RedisDraftStorage(scenario_id, request.user.id)
        # if storage:
        #     # Применяем черновики к БД
        #     storage.commit_changes()
        # return Response(status=status.HTTP_200_OK)
        try:
            storage = RedisDraftStorage(scenario_id, request.user.id)
            if storage:
                # Применяем черновики к БД
                storage.commit_changes()
            return Response(status=status.HTTP_200_OK)
        except ValueError as e:
            # logger.exception(e)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # logger.exception(e)
            return Response(
                {"error":  str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )