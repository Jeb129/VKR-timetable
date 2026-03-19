# from rest_framework.views import APIView
# from rest_framework import viewsets, status
# from rest_framework.response import Response
# from .serializers import BuildingSerializer, TeacherSerializer, StudyGroupSerializer, LessonSerializer, BookingSerializer


# class HealthCheckView(APIView):
#     def get(self, request):
#         return Response({"status": "ok"})

# class BuildingViewSet(viewsets.ModelViewSet):
#     queryset = Building.objects.all()
#     serializer_class = BuildingSerializer

# class ClassroomViewSet(viewsets.ModelViewSet):
#     queryset = Classroom.objects.all()
#     serializer_class = ClassroomSerializer

# class TeacherViewSet(viewset.ModelViewSet):
#     queryset = Teacher.objects.all()
#     serializer_class = TeacherSerializer

# class StudyGroupViewSet(viewsets.ModelViewSet):
#     queryset = StudyGroup.objects.all()
#     serializer_class = StudyGroupSerializer

# class LessonViewSet(viewsets.ModelViewSet):
#     queryset = Lesson.objects.all()
    
#     def get_serializer_class(self):
#         # Используем детальный сериализатор для просмотра и обычный для создания
#         if self.action in ['list', 'retrieve']:
#             return LessonSerializer
#         return LessonSerializer

# class BookingViewSet(viewsets.ModelViewSet):
#     queryset = Booking.objects.all()
#     serializer_class = BookingSerializer