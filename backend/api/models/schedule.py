from django.db import models
from django.db.models import Q
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import RangeOperators
from django.core.exceptions import ValidationError

from api.models.enums import WeekCycle, Weekday

class Semester(models.Model):
    """Для отображения расписания в календаре"""

    name = models.CharField(max_length=255, unique=True, verbose_name="наименование")
    date_start = models.DateField(null=False, unique=True, verbose_name="дата начала")
    date_end = models.DateField(null=False, unique=True, verbose_name="дата окончания")

    class Meta:
        ordering = ["date_start"]
        verbose_name = "семестр"
        verbose_name_plural = "семестры"
        
        constraints = [
            # пересечение периодов
            ExclusionConstraint(
                name='exclude_overlapping_semesters',
                expressions=[
                    (models.Func('date_start', 'date_end', models.Value('[]'), function='daterange'), RangeOperators.OVERLAPS),
                ],
            ),

            models.CheckConstraint(
                condition=models.Q(date_start__lt=models.F('date_end')),
                name='check_start_before_end'
            ),
        ]

    def clean(self):
        if self.date_start and self.date_end and self.date_start >= self.date_end:
            raise ValidationError("Дата начала должна быть меньше даты окончания")
        
        overlap = Semester.objects.filter(
            date_start__lt=self.date_end,
            date_end__gt=self.date_start
        ).exclude(pk=self.pk)
        
        if overlap.exists():
            raise ValidationError(f"Период пересекается с существующим семестром: {overlap.first()}")
        
    def __str__(self) -> str:
        return self.name


class ScheduleScenario(models.Model):
    """Варианты расписания"""

    name = models.CharField(max_length=255, verbose_name="наименование")
    semester = models.ForeignKey(
        Semester, on_delete=models.SET_NULL, null=True, verbose_name="семестр"
    )  # Для ограничения. Возможно сюр, но пока так
    is_active = models.BooleanField(default=False, verbose_name="действующий")
    total_penalty = models.IntegerField(default=0, verbose_name="штраф по ограничениям")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="время создания")

    def __str__(self) -> str:
        return f"({self.semester}) {self.name}"

    class Meta:
        ordering = ["semester", "is_active", "name"]
        verbose_name = "вариант расписания"
        verbose_name_plural = "варианты расписания"
        constraints = [
            # Одно активное расписание на семестр
            models.UniqueConstraint(
                fields=["semester"],
                condition=models.Q(is_active=True),
                name="unique_active_record",
            )
        ]


class Timeslot(models.Model):
    day = models.PositiveSmallIntegerField(
        choices=Weekday.choices, 
        verbose_name="день недели"
    )
    week_num = models.PositiveSmallIntegerField(
        choices=WeekCycle.choices, # На всякий ограничил 2 вариантами, т.к полноценный цикл я не везде писал 
        verbose_name="номер недели в цикле"
    )
    order_number = models.PositiveSmallIntegerField(default=1, verbose_name="номер пары")  # Номер пары
    time_start = models.TimeField(verbose_name="время начала")
    time_end = models.TimeField(verbose_name="время окончания")

    class Meta:
        ordering = ["week_num", "day", "time_start"]
        verbose_name = "слот расписания"
        verbose_name_plural = "слоты расписания"

        constraints = [
            # Проверка, что время начала раньше времени окончания
            models.CheckConstraint(
                condition=models.Q(time_start__lt=models.F('time_end')),
                name='timeslot_start_before_end'
            ),
            # Уникальность слота: не может быть двух "первых пар" в один день одной недели
            models.UniqueConstraint(
                fields=['day', 'week_num', 'order_number'],
                name='unique_timeslot_order'
            ),
            # Ограничение значений (пн-сб: 1-6, недели: 1-2)
            models.CheckConstraint(
                condition=models.Q(day__gte=1, day__lte=7),
                name='valid_day'
            )
        ]

    def __str__(self):
        return f"{self.order_number} пара ({self.get_week_num_display()}, {self.get_day_display()})"
