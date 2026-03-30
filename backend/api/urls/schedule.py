from django.urls import path
from api.views import TeacherScheduleView, GroupScheduleView, ClassroomScheduleView

urlpatterns =[
    path("group/",GroupScheduleView.as_view(), name="group_schedule"),
    path("teacher/", TeacherScheduleView.as_view(), name="teacher_schedule"),
    path("classroom/",ClassroomScheduleView.as_view(), name="classroom_schedule")
]

