from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from api.models import Lesson, ScheduleScenario
from api.serializers import LessonSerializer
from api.serializers.schedule import ConstraintErrorSerializer
from api.services.constraunt.manager import ConstraintManager
from api.services.redis.storage import RedisDraftStorage
from api.services.schedule.draft.context import draft_context
from config.utils import normalize_diff

class DraftScenarioView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, scenario_id: int):
        scenario = get_object_or_404(ScheduleScenario, id=scenario_id)
        storage = RedisDraftStorage(scenario_id, request.user.id)
        
        group_id = request.query_params.get("group_id")
        teacher_id = request.query_params.get("teacher_id")
        with draft_context(scenario, storage):
            queryset = Lesson.objects.all()
            if group_id:
                queryset = queryset.filter(study_groups__id=int(group_id))
            elif teacher_id:
                queryset = queryset.filter(teachers__id=int(teacher_id))
            serialized = LessonSerializer(queryset, many=True).data

        return Response({
            "lessons": serialized,
            "has_draft": storage.has_any_changes(),
        },status=status.HTTP_200_OK)
    
    def put(self, request, scenario_id: int):
        lesson_id = self.request.query_params.get("lesson_id")
        get_object_or_404(ScheduleScenario, id=scenario_id)
        storage = RedisDraftStorage(scenario_id, request.user.id)

        # Готовый метод в commit_scenario
        errors= ConstraintManager().load().prepare_draft_lesson(
            scenario_id=scenario_id,
            lesson_id=lesson_id,
            data=normalize_diff(Lesson,request.data),
            storage=storage
        )
        return Response({
            # "errors": len(errors),
            "errors": ConstraintErrorSerializer(errors, many = True).data,
        })
    def post(self, request, scenario_id: int):
        get_object_or_404(ScheduleScenario, id=scenario_id)
        storage = RedisDraftStorage(scenario_id, request.user.id)
        new_id = storage.create_lesson(data=normalize_diff(Lesson,request.data))
        
        errors= ConstraintManager().load().check_lesson_draft(
            scenario_id=scenario_id,
            lesson_id=new_id,
            storage=storage
        )

        return Response({
            "id": new_id,
            "errors": [e for e in errors],
        },status=status.HTTP_201_CREATED)
    

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