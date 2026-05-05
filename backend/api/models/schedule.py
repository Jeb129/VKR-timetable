from django.db import models


class Semester(models.Model):
    """Для отображения расписания в календаре"""

    name = models.CharField(max_length=255, unique=True, verbose_name="наименование")
    date_start = models.DateField(null=False, unique=True, verbose_name="дата начала")
    date_end = models.DateField(null=False, unique=True, verbose_name="дата окончания")

    class Meta:
        ordering = ["date_start"]
        verbose_name = "семестр"
        verbose_name_plural = "семестры"

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
    day = models.PositiveSmallIntegerField(verbose_name="день")  # 1-6
    week_num = models.PositiveSmallIntegerField(verbose_name="номер недели в цикле")  # 1-2
    order_number = models.PositiveSmallIntegerField(default=1, verbose_name="номер пары")  # Номер пары
    time_start = models.TimeField(verbose_name="время начала")
    time_end = models.TimeField(verbose_name="время окончания")

    class Meta:
        ordering = ["week_num", "day", "time_start"]
        verbose_name = "слот расписания"
        verbose_name_plural = "слоты расписания"

    def __str__(self):
        days = ["пн","вт","ср","чт","пт","сб","вм"]
        return f"{self.order_number} пара ({"числитель" if self.week_num else "знаменатель"}, {days[self.day]})"
