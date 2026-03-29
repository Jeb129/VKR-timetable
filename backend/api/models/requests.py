# Модели, связанные с заявками

from django.db import models

from api.models import enums
from api.models.buildings import Classroom
from api.models.models import Teacher
from api.models.schedule import Discipline, Lesson, LessonType, Timeslot
from authentification.models import CustomUser

class Request(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.IntegerField(
        choices=enums.RequestStatus.choices,
        default=enums.RequestStatus.ON_MODERATION,
        db_index=True
    )
    request_type = models.IntegerField(choices=enums.RequestType.choices, null=True)

class ExcludedTimeslot(Request):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    timeslot = models.ForeignKey(Timeslot, on_delete=models.CASCADE)
    
    def save(self, *args, **kwargs):
        self.request_type = enums.RequestType.ExcludedTimeslot
        super().save(*args, **kwargs)

class ClassroomPreference(Request):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE)
    lesson_type = models.ForeignKey(LessonType, on_delete=models.CASCADE)
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    
    def save(self, *args, **kwargs):
        self.request_type = enums.RequestType.ClassroomPreference
        super().save(*args, **kwargs)

class Booking(Request):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    date_start = models.DateTimeField()
    date_end = models.DateTimeField()

    def save(self, *args, **kwargs):
        self.request_type = enums.RequestType.Booking
        super().save(*args, **kwargs)

class ScheduleAdjustment(Request):
    date = models.DateField()
    timeslot = models.ForeignKey(Timeslot, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        self.request_type = enums.RequestType.ScheduleAdjustment
        super().save(*args, **kwargs)