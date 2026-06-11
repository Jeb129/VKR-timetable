from django.urls import path, include 
from rest_framework.routers import DefaultRouter
from api.views import (TeacherScheduleView, 
                       GroupScheduleView, 
                       ClassroomScheduleView)

router = DefaultRouter()

urlpatterns =[
    path("group/",GroupScheduleView.as_view(), name="group_schedule"),
    path("teacher/", TeacherScheduleView.as_view(), name="teacher_schedule"),
    path("classroom/",ClassroomScheduleView.as_view(), name="classroom_schedule"),
    path('', include(router.urls)),
]

