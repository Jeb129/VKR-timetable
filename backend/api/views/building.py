from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from api.models import Classroom
from api.serializers import ClassroomSerializer


class ClassroomViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Classroom.objects.all().order_by("num")
    serializer_class = ClassroomSerializer
    permission_classes = [AllowAny]
