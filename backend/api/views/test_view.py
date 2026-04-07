

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models.schedule import Lesson
from api.serializers.education import LessonSerializer
from api.services.redis.storage import RedisDraftStorage
from api.services.constraunt.manager import ConstraintManager
from api.services.schedule.draft.context import draft_context

class TestDraftScenarioView(APIView):
    def get(self, request):
        data = None

        storage = RedisDraftStorage(1,1)
        # data = storage.list_changes()

        with draft_context(1, storage) as manager:
            draft = Lesson.objects.get(id=1)
            data = LessonSerializer(draft).data

        return Response(data,status=status.HTTP_200_OK)
    
    def post(self, request):
        RedisDraftStorage(1,1).clear_all()
        return Response(status=status.HTTP_200_OK)