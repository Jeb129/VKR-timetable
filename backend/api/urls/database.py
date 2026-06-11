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
)

router = DefaultRouter()
router.register(r'classrooms', ClassroomViewSet, basename='classroom')
router.register(r'timeslots', TimeslotViewSet, basename='timeslot')
router.register(r'scenarios', ScheduleScenarioViewSet, basename='scenario')
router.register(r'groups', StudyGroupViewSet, basename='group')
router.register(r'teachers', TeacherViewSet, basename='teacher')
router.register(r'requests', RequestViewSet, basename='request')
router.register(r'disciplines', DisciplineViewSet, basename='discipline')
router.register(r'lesson-types', LessonTypeViewSet, basename='lesson-type')
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
