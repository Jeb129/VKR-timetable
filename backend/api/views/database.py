from rest_framework import viewsets, filters
from api.models import *
from api.pagination import StandartPagination
from api.serializers import *

class BaseReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    """Базовый класс для ReadOnly ViewSet с общей конфигурацией"""
    pagination_class = StandartPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]

class InstituteViewSet(BaseReadOnlyViewSet):
    queryset = Institute.objects.all()
    serializer_class = InstituteSerializer
    search_fields = ['name', 'short_name']

class StudyProgramViewSet(BaseReadOnlyViewSet):
    queryset = StudyProgram.objects.select_related('institute').all()
    serializer_class = StudyProgramSerializer
    search_fields = ['code', 'name', 'short_name']

class StudyGroupViewSet(BaseReadOnlyViewSet):
    queryset = StudyGroup.objects.select_related('study_program').prefetch_related('sub_groups').all()
    serializer_class = StudyGroupSerializer
    search_fields = ['name', 'group_num']

class AcademicLoadViewSet(BaseReadOnlyViewSet):
    queryset = AcademicLoad.objects.select_related(
        'discipline', 'teacher', 'study_group', 'semester', 'lesson_type'
    ).all()
    serializer_class = AcademicLoadSerializer
    search_fields = ['discipline__name', 'teacher__name', 'study_group__name', 'merge_key']

class TeacherViewSet(BaseReadOnlyViewSet):
    queryset = Teacher.objects.select_related('institute').all()
    serializer_class = TeacherSerializer
    search_fields = ['name', 'post']

class TimeslotViewSet(BaseReadOnlyViewSet):
    queryset = Timeslot.objects.all()
    serializer_class = TimeslotSerializer
    search_fields = ['order_number']

class DisciplineViewSet(BaseReadOnlyViewSet):
    queryset = Discipline.objects.all()
    serializer_class = DisciplineSerializer
    search_fields = ['name']

class SemesterViewSet(BaseReadOnlyViewSet):
    queryset = Semester.objects.all()
    serializer_class = SemesterSerializer
    search_fields = ['name']

class LessonTypeViewSet(BaseReadOnlyViewSet):
    queryset = LessonType.objects.all()
    serializer_class = LessonTypeSerializer
    search_fields = ['name', 'short_name']

class BuildingViewSet(BaseReadOnlyViewSet):
    queryset = Building.objects.all()
    serializer_class = BuildingSerializer
    search_fields = ['name', 'short_name', 'address']

class ClassroomViewSet(BaseReadOnlyViewSet):
    queryset = Classroom.objects.select_related('building').all()
    serializer_class = ClassroomSerializer
    search_fields = ['num', 'name', 'building__name', 'building__short_name']

class ClassroomBookingAbleViewSet(ClassroomViewSet):
    queryset = Classroom.objects.filter(allow_booking=True).select_related('building')

class ClassroomLessonAbleViewSet(ClassroomViewSet):
    queryset = Classroom.objects.filter(allow_lessons=True).select_related('building')

class EquipmentViewSet(BaseReadOnlyViewSet):
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer
    search_fields = ['name']

class BookingTypeViewSet(BaseReadOnlyViewSet):
    queryset = BookingType.objects.all()
    serializer_class = BookingTypeSerializer
    search_fields = ['name']

class BuildingTravelTimeViewSet(BaseReadOnlyViewSet):
    queryset = BuildingTravelTime.objects.select_related('from_building', 'to_building').all()
    serializer_class = BuildingTravelTimeSerializer
    search_fields = ['from_building__name', 'to_building__name']

class ConstraintViewSet(BaseReadOnlyViewSet):
    queryset = Constraint.objects.all()
    serializer_class = ConstraintSerializer
    search_fields = ['name', 'description']

class ClassroomPreferenceViewSet(BaseReadOnlyViewSet):
    queryset = ClassroomPreference.objects.select_related(
        'teacher', 'discipline', 'lesson_type', 'classroom'
    ).all()
    serializer_class = ClassroomPreferenceSerializer
    search_fields = ['teacher__name', 'discipline__name', 'classroom__name']

class LessonViewSet(BaseReadOnlyViewSet):
    queryset = Lesson.objects.select_related(
        'scenario', 'discipline', 'lesson_type', 'timeslot', 'classroom'
    ).prefetch_related('teachers', 'study_groups').all()
    serializer_class = LessonSerializer
    search_fields = ['discipline__name', 'classroom__name', 'teachers__name', 'study_groups__name']