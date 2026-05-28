# Модели, связанные с заявками
from django.db import models

from api.models import enums
from api.models.academic_load import Lesson
from api.models.buildings import Classroom
from api.models.education_subjects import Discipline, LessonType, Teacher
from api.models.schedule import Timeslot
from authentification.models import CustomUser


class Request(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    admin_comment = models.TextField(
        null=True, blank=True, help_text="Причина отказа или заметка модератора"
    )
    status = models.IntegerField(
        choices=enums.RequestStatus.choices,
        default=enums.RequestStatus.ON_MODERATION,
        db_index=True,
    )
    request_type = models.IntegerField(choices=enums.RequestType.choices, null=True)


class ExcludedTimeslot(Request):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    timeslot = models.ForeignKey(Timeslot, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        self.request_type = enums.RequestType.EXCLUDED_TIMESLOT
        super().save(*args, **kwargs)


class ClassroomPreference(Request):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE)
    lesson_type = models.ForeignKey(LessonType, on_delete=models.CASCADE)
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        self.request_type = enums.RequestType.CLASSROOM_PREFERENCE
        super().save(*args, **kwargs)

class BookingType(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Тип мероприятия")

    def __str__(self):
        return self.name

class Booking(Request):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    booking_type = models.ForeignKey(BookingType, on_delete=models.PROTECT, null=True, verbose_name="Тип брони")
    date_start = models.DateTimeField()
    date_end = models.DateTimeField()

    def save(self, *args, **kwargs):
        self.request_type = enums.RequestType.BOOKING
        super().save(*args, **kwargs)

    def __str__(self):
        b_type = self.booking_type.name if self.booking_type else "Мероприятие"
        return f"{b_type}: {self.description[:30]}"

# Корректировка расписания позволяет либо снять, либо переместить занятие в сетке
# Заменяет timeslot в занятии на timeslot в записи
# Для снятия нужно создать запись с пустым timeslot
# Перенос между днями создает 2 записи:
# С пустым слотом, чтобы снять занятие с одного дня
# С измененным, чтобы поставить в другой день\


class ScheduleAdjustment(models.Model):
    request = models.ForeignKey(Request,null=False, on_delete=models.CASCADE)
    # Определяеем дату изменения
    date = models.DateField()
    # Определяем изменяемое занятие
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)

    # Новое время занятия. Null если нужно снять занятие
    timeslot = models.ForeignKey(Timeslot,null=True, on_delete=models.CASCADE)
    classroom = models.ForeignKey(Classroom,null=True, on_delete=models.CASCADE)
