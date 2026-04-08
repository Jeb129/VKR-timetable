from rest_framework.routers import DefaultRouter
from api.views import (
    ClassroomViewSet, 
    BookingViewSet,
    TimeslotViewSet,
    ScheduleScenarioViewSet,
    StudyGroupViewSet,
    TeacherViewSet
    )

router = DefaultRouter()
router.register(r'classrooms', ClassroomViewSet, basename='classroom')
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'timeslots', TimeslotViewSet, basename='timeslot')
router.register(r'scenarios', ScheduleScenarioViewSet, basename='scenario')
router.register(r'groups', StudyGroupViewSet, basename='group')
router.register(r'teachers', TeacherViewSet, basename='teacher')

urlpatterns = router.urls