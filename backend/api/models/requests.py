# Модели, связанные с заявками
from django.db import models

from api.models import enums
from api.models.academic_load import Lesson
from api.models.buildings import Classroom
from api.models.education_subjects import Discipline, LessonType, Teacher
from api.models.schedule import Timeslot
from authentification.models import CustomUser


class Request(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name="Автор")
    description = models.TextField(verbose_name="Описание")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время создания")
    admin_comment = models.TextField(
        null=True, blank=True, help_text="Причина отказа или заметка модератора", verbose_name="Комментарий администратора"
    )
    status = models.IntegerField(
        choices=enums.RequestStatus.choices,
        default=enums.RequestStatus.PENDING,
        db_index=True, verbose_name="Статус"
    )
    type = models.IntegerField(choices=enums.RequestType.choices, null=True, verbose_name="Вид заявки")

    @property
    def get_child_obj(self):
        if self.type == enums.RequestType.EXCLUDED_TIMESLOT: return self.excludedtimeslot
        if self.type == enums.RequestType.CLASSROOM_PREFERENCE:return self.classroompreference
        if self.type == enums.RequestType.SCHEDULE_ADJUSTMENT: return self.scheduleadjustment_set
        if self.type == enums.RequestType.BOOKING: return self.booking

    class Meta:
        ordering = ["created_at"]
        verbose_name = "заявка"
        verbose_name_plural = "заявки"

class ExcludedTimeslot(Request):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, verbose_name="Преподаватель")
    timeslot = models.ForeignKey(Timeslot, on_delete=models.CASCADE, verbose_name="Временной слот")

    def save(self, *args, **kwargs):
        self.type = enums.RequestType.EXCLUDED_TIMESLOT
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ["teacher"]
        verbose_name = "исключенный слот расписания"
        verbose_name_plural = "исключенные слоты расписания"


class ClassroomPreference(Request):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, verbose_name="преподаватель")
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE, verbose_name="дисциплина")
    lesson_type = models.ForeignKey(LessonType, on_delete=models.CASCADE, verbose_name="вид занятия")
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, verbose_name="аудитория")

    def save(self, *args, **kwargs):
        self.type = enums.RequestType.CLASSROOM_PREFERENCE
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ["teacher"]
        verbose_name = "предпочтение преподавателя по аудитории"
        verbose_name_plural = "предпочтения преподавателей по аудитории"

class BookingType(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Наименование")

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ["name"]
        verbose_name = "вид мероприятия"
        verbose_name_plural = "виды мероприятий"

class Booking(Request):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, verbose_name="аудитория")
    booking_type = models.ForeignKey(BookingType, on_delete=models.PROTECT, null=True, verbose_name="вид мероприятия")
    date_start = models.DateTimeField(verbose_name="начало мероприятия")
    date_end = models.DateTimeField(verbose_name="конец мероприятия")

    class Meta:
        constraints = [
            # Время начала строго раньше времени конца
            models.CheckConstraint(
                condition=models.Q(date_start__lt=models.F('date_end')),
                name='booking_start_before_end'
            ),
        ]
        verbose_name = "бронирование"
        verbose_name_plural = "бронирования"

    def save(self, *args, **kwargs):
        self.type = enums.RequestType.BOOKING
        super().save(*args, **kwargs)

    def __str__(self):
        b_type = self.booking_type.name if self.booking_type else "Бронирования"
        return f"{b_type}: {self.description[:30]}"

# Корректировка расписания позволяет либо снять, либо переместить занятие в сетке
# Заменяет timeslot в занятии на timeslot в записи
# Для снятия нужно создать запись с пустым timeslot
# Перенос между днями создает 2 записи:
# С пустым слотом, чтобы снять занятие с одного дня
# С измененным, чтобы поставить в другой день\


class ScheduleAdjustment(models.Model):
    request = models.ForeignKey(Request,null=False, on_delete=models.CASCADE, verbose_name="заявки")
    # Определяеем дату изменения
    date = models.DateField(verbose_name="дата занятия")
    # Определяем изменяемое занятие
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, verbose_name="исходное занятие")

    # Новое время занятия. Null если нужно снять занятие
    timeslot = models.ForeignKey(Timeslot,null=True, blank=True, on_delete=models.CASCADE, verbose_name="новое время")
    classroom = models.ForeignKey(Classroom,null=True, blank=True, on_delete=models.CASCADE, verbose_name="новая аудитория")

    class Meta:
        verbose_name = "корректировка расписания"
        verbose_name_plural = "корректировки расписания"