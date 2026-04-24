from django.urls import path, include 
from rest_framework.routers import DefaultRouter
from api.views import (TeacherScheduleView, 
                       GroupScheduleView, 
                       ClassroomScheduleView, 
                       MyTeacherScheduleView, 
                       ScheduleAdjustmentCreateView,
                       ScheduleAdjustmentViewSet)

router = DefaultRouter()
router.register(r'adjustments', ScheduleAdjustmentViewSet, basename='adjustment')

urlpatterns =[
    path("group/",GroupScheduleView.as_view(), name="group_schedule"),
    path("teacher/", TeacherScheduleView.as_view(), name="teacher_schedule"),
    path("classroom/",ClassroomScheduleView.as_view(), name="classroom_schedule"),
    path("adjustment/", ScheduleAdjustmentCreateView.as_view(), name="adjustment_create"),
    path("teacher/my/", MyTeacherScheduleView.as_view(), name="my_teacher_schedule"),
    path('', include(router.urls)),
]

