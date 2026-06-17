from django.db import models


class Building(models.Model):
    name = models.CharField(max_length=50, verbose_name="наименование")
    short_name = models.CharField(max_length=5, verbose_name="сокращение")
    address = models.CharField(null=True,max_length=255, verbose_name="адрес")
    ymap_key = models.CharField(null=True,max_length=255, verbose_name="ключ карты")
    work_start_time = models.TimeField(verbose_name="начало рабочего дня")
    work_end_time = models.TimeField(verbose_name="конец рабочего дня")

    class Meta:
        verbose_name = "корпус"
        verbose_name_plural = "корпуса"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(work_start_time__lt=models.F('work_end_time')),
                name='building_check_start_before_end'
            ),
        ]

    def __str__(self):
        return f"Корпус {self.short_name}"


class Equipment(models.Model):
    name = models.CharField(max_length=100, verbose_name="наименование")

    class Meta:
        verbose_name = "оборудование"
        verbose_name_plural = "оборудование"

    def __str__(self):
        return self.name


class Classroom(models.Model):
    building = models.ForeignKey(
        Building,
        on_delete=models.SET_NULL,
        related_name="classrooms",
        null=True,
        blank=True,
        verbose_name="корпус",
    )
    num = models.CharField(max_length=20, verbose_name="номер")
    name = models.CharField(max_length=100, blank=True, verbose_name="наименование")
    capacity = models.PositiveIntegerField(verbose_name="вместимость")
    eios_id = models.IntegerField(
        null=True,
        blank=True,
        unique=True,
        help_text="ID аудитории в системе EIOS",
        verbose_name="EIOS ID",
    )
    equipment = models.ManyToManyField(
        "Equipment", blank=True, related_name="classrooms", verbose_name="оснащение"
    )
    allow_parallel = models.BooleanField(
        default=False, verbose_name="разрешить парралельные занятия"
    )
    is_virtual = models.BooleanField(
        default=False, verbose_name="виртуальная аудитория"
    )
    allow_lessons = models.BooleanField(
        default=True, verbose_name="разрешить проводить занятия в аудитории"
    )
    allow_booking = models.BooleanField(
        default=True, verbose_name="разрешить бронировать аудиторию для проведения мероприятий"
    )

    class Meta:
        verbose_name = "аудитория"
        verbose_name_plural = "аудитории"
        constraints = [
            # Уникальность номеров в корпусе
            models.UniqueConstraint(
                fields=['building', 'num'], 
                name='classroom_unique_number'
            ),
        ]
        ordering = ["building_id","num"]

    def save(self, *args, **kwargs):
        if not self.name and self.building:
            self.name = f"{self.building.short_name}-{self.num}"
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class BuildingTravelTime(models.Model):
    from_building = models.ForeignKey(
        Building,
        on_delete=models.CASCADE,
        related_name="travel_from",
        verbose_name="стартовый корпус",
    )
    to_building = models.ForeignKey(
        Building,
        on_delete=models.CASCADE,
        related_name="travel_to",
        verbose_name="конечный корпус",
    )
    travel_time_minutes = models.PositiveIntegerField(
        verbose_name="Время перехода (в минутах)"
    )

    class Meta:
        verbose_name = "время перехода между корпусами"
        verbose_name_plural = "время перехода между корпусами"

        constraints = [
            # Уникальность пары корпусов
            models.UniqueConstraint(
                fields=['from_building', 'to_building'], 
                name='unique_building_travel'
            ),
            # Нельзя ехать из корпуса в тот же самый корпус
            models.CheckConstraint(
                condition=~models.Q(from_building=models.F('to_building')),
                name='prevent_self_travel'
            )
        ]
