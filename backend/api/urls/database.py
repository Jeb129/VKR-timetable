from rest_framework.routers import DefaultRouter

from api.views import (
    AcademicLoadViewSet,
    BookingTypeViewSet,
    BuildingTravelTimeViewSet,
    BuildingViewSet,
    ClassroomPreferenceViewSet,
    ClassroomViewSet,
    ConstraintViewSet,
    DisciplineViewSet,
    EquipmentViewSet,
    InstituteViewSet,
    LessonTypeViewSet,
    LessonViewSet,
    RequestViewSet,
    ScheduleScenarioViewSet,
    StudyGroupViewSet,
    StudyProgramViewSet,
    TeacherViewSet,
    TimeslotViewSet,
    SemesterViewSet,
)

router = DefaultRouter()
router.register(r'classrooms', ClassroomViewSet, basename='classrooms')
router.register(r'timeslots', TimeslotViewSet, basename='timeslots')
router.register(r'scenarios', ScheduleScenarioViewSet, basename='scenarios')
router.register(r'groups', StudyGroupViewSet, basename='groups')
router.register(r'semesters', SemesterViewSet, basename='semesters')
router.register(r'teachers', TeacherViewSet, basename='teachers')
router.register(r'requests', RequestViewSet, basename='requests')
router.register(r'disciplines', DisciplineViewSet, basename='disciplines')
router.register(r'lesson-types', LessonTypeViewSet, basename='lesson-types')
router.register(r'institutes', InstituteViewSet)
router.register(r'programs', StudyProgramViewSet)
router.register(r'academic-loads', AcademicLoadViewSet)
router.register(r'buildings', BuildingViewSet)
router.register(r'equipment', EquipmentViewSet)
router.register(r'booking-types', BookingTypeViewSet)
router.register(r'travel-times', BuildingTravelTimeViewSet)
router.register(r'constraints', ConstraintViewSet)
router.register(r'classroom-preferences', ClassroomPreferenceViewSet)
router.register(r'lessons', LessonViewSet)

urlpatterns = router.urls
