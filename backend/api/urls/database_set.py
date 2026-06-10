from rest_framework.routers import DefaultRouter
from api.views import (
    ClassroomViewSet, 
    TimeslotViewSet,
    ScheduleScenarioViewSet,
    StudyGroupViewSet,
    TeacherViewSet,
    DisciplineViewSet,
    LessonTypeViewSet,
    RequestViewSet
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

urlpatterns = router.urls