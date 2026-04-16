#ИУи можено писать всякую хрень которую надо тестить, но лень поднимать фронт

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from api.models import Lesson, ScheduleScenario
# from api.serializers.education import LessonSerializer
from api.services.redis.storage import RedisDraftStorage
from api.services.constraunt.manager import ConstraintManager
from api.services.schedule.draft.context import draft_context
from config.utils import normalize_diff

class TestDraftScenarioView(APIView):
    def get(self, request):
        data = None
        
        storage = RedisDraftStorage(1,0)
        # storage.update_lesson(1,{
        #     "classroom":2,
        # })
        # data = storage.list_changes()
        # with draft_context(1, storage) as manager:
        #     # draft = Lesson.objects.filter(classroom__id=1)
        #     # draft = Lesson.objects.filter(classroom_id=1)
        #     draft = Lesson.objects.filter(classroom__id=2).filter(timeslot__day=3)
        #     # data = []
        #     # for d in Lesson.objects.all():
        #     #     data.append(LessonSerializer(d).data)
        #     # print(draft.count())

        #     data = LessonSerializer(draft, many=True).data
        data = ConstraintManager.load().prepare_draft_lesson(
            scenario_id=1,
            lesson_id=1,
            data=normalize_diff(Lesson,request.data),
            storage=storage
        )

        # orig =LessonSerializer(Lesson.objects.get(id=1)).data    

        return Response({"draft":data},status=status.HTTP_200_OK)
    
    def put(self, request,):
        scenario_id = 1
        lesson_id = 1
        # lesson_id = self.request.query_params.get("lesson_id")
        get_object_or_404(ScheduleScenario, id=scenario_id)
        storage = RedisDraftStorage(scenario_id, 0)

        # Готовый метод в ConstraintManager
        errors= ConstraintManager.load().prepare_draft_lesson(
            scenario_id=scenario_id,
            lesson_id=lesson_id,
            data=normalize_diff(Lesson,request.data),
            storage=storage
        )

        return Response({
            "errors": [e for e in errors],
        })
    def post(self, request):
        RedisDraftStorage(1,1).clear_all()
        return Response(status=status.HTTP_200_OK)