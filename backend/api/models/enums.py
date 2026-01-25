# Файл используется для хранения перечислений, которые не хранятся в БД
# Статусы заявок, формы обучения и т.д.

from django.db import models

class RequestStatus(models.IntegerChoices):
    ON_MODERATION = 0, 'На модерации'
    VERIFIED = 1, 'Одобрена'
    REJECTED = 2, 'Отклонена'
    CANCELED = 3, 'Отменена'

class RequestType(models.IntegerChoices):
    ExcludedTimeslot = 0, "Исключение времени занятия"
    ClassroomPreference = 1, "Предпочтения по аудитории"
    ScheduleAdjustment = 2, "Изменение в расписании"
    Booking = 3, "Бронирование аудитории"