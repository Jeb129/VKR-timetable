"""Файл используется для хранения перечислений, которые не хранятся в БД
Статусы заявок, формы обучения и т.д."""

from django.db import models
from django.utils.translation import gettext_lazy as _


class GenerationStatus(models.IntegerChoices):
    SUCESS = 0, _("Готово")
    IN_PROGRESS = 1, _("В процессе")
    ERROR = 2, _("Ошибка")
    INFEASIBLE = 3, _("Нерешаемый")


class WeekCycle(models.IntegerChoices):
    UPPER = 1, _("Числитель")
    LOWER = 2, _("Знаменатель")

class Weekday(models.IntegerChoices):
    """Дни недели"""

    MONDAY = 1, _("Понедельник")
    TUESDAY = 2, _("Вторник")
    WEDNESDAY = 3, _("Среда")
    THURSDAY = 4, _("Четверг")
    FRIDAY = 5, _("Пятница")
    SATURDAY = 6, _("Суббота")
    SUNDAY = 7, _("Воскресенье")

class RequestStatus(models.IntegerChoices):
    """Статусы заявок"""

    PENDING = 0, _("На модерации")
    VERIFIED = 1, _("Одобрена")
    REJECTED = 2, _("Отклонена")
    CANCELED = 3, _("Отменена")


class RequestType(models.IntegerChoices):
    """Типы заявок"""

    EXCLUDED_TIMESLOT = 0, _("Исключение времени занятия")
    CLASSROOM_PREFERENCE = 1, _("Предпочтения по аудитории")
    SCHEDULE_ADJUSTMENT = 2, _("Изменение в расписании")
    BOOKING = 3, _("Бронирование аудитории")


class EventType(models.IntegerChoices):
    """Типы событий"""

    LESSON = 0, _("Учебное занятие")
    SCHEDULE_ADJUSTMENT = 1, _("Изменение в расписании")
    BOOKING = 2, _("Бронирование аудитории")
