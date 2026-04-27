from django.db import models


class Semester(models.Model):
    """Для отображения расписания в календаре"""

    name = models.CharField(max_length=255, unique=True)
    date_start = models.DateField(null=False, unique=True)
    date_end = models.DateField(null=False, unique=True)

    def __str__(self) -> str:
        return self.name


class ScheduleScenario(models.Model):
    """Варианты расписания"""

    name = models.CharField(max_length=255)
    semester = models.ForeignKey(
        Semester, on_delete=models.SET_NULL, null=True
    )  # Для ограничения. Возможно сюр, но пока так
    is_active = models.BooleanField(default=False)
    total_penalty = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name

    class Meta:
        constraints = [
            # Одно активное расписание на семестр
            models.UniqueConstraint(
                fields=["semester"],
                condition=models.Q(is_active=True),
                name="unique_active_record",
            )
        ]


class Timeslot(models.Model):
    day = models.PositiveSmallIntegerField()  # 1-6
    week_num = models.PositiveSmallIntegerField()  # 1-2
    order_number = models.PositiveSmallIntegerField(default=1)  # Номер пары
    time_start = models.TimeField()
    time_end = models.TimeField()

    def __str__(self):
        return f"День {self.day} | Пара {self.order_number}"
