"""Файл используется для хранения перечислений, которые не хранятся в БД
Статусы заявок, формы обучения и т.д."""

from django.db import models


class RequestStatus(models.IntegerChoices):
    """Статусы заявок"""
    ON_MODERATION = 0, "На модерации"
    VERIFIED = 1, "Одобрена"
    REJECTED = 2, "Отклонена"
    CANCELED = 3, "Отменена"


class RequestType(models.IntegerChoices):
    """Типы заявок"""
    EXCLUDED_TIMESLOT = 0, "Исключение времени занятия"
    CLASSROOM_PREFERENCE = 1, "Предпочтения по аудитории"
    SCHEDULE_ADJUSTMENT = 2, "Изменение в расписании"
    BOOKING = 3, "Бронирование аудитории"
