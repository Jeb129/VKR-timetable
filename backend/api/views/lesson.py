from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from api.models import StudyGroup, Teacher
from api.serializers import StudyGroupSerializer, TeacherSerializer 

class StudyGroupViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StudyGroup.objects.all().order_by("name")
    serializer_class = StudyGroupSerializer
    permission_classes = [AllowAny]

class TeacherViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Teacher.objects.all().order_by("name")
    serializer_class = TeacherSerializer
    permission_classes = [AllowAny]