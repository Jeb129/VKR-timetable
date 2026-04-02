from django.db import models


class Building(models.Model):
    name = models.CharField(max_length=50)
    short_name = models.CharField(max_length=5)
    address = models.CharField(max_length=255)
    work_start_time = models.TimeField()
    work_end_time = models.TimeField()

    def __str__(self):
        return self.name


class Equipment(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Classroom(models.Model):
    building = models.ForeignKey(
        Building,
        on_delete=models.SET_NULL,
        related_name="classrooms",
        null=True,
        blank=True,
    )
    num = models.CharField(max_length=20)
    name = models.CharField(max_length=100, blank=True)
    capacity = models.PositiveIntegerField()
    eios_id = models.IntegerField(
        null=True, blank=True, unique=True, help_text="ID аудитории в системе EIOS"
    )
    equipment = models.ManyToManyField(
        "Equipment", blank=True, related_name="classrooms"
    )

    def __str__(self):
        if self.building is None:
            return self.name
        return f"{self.building.short_name} - {self.num}"


class BuildingTravelTime(models.Model):
    from_building = models.ForeignKey(
        Building, on_delete=models.CASCADE, related_name="travel_from"
    )
    to_building = models.ForeignKey(
        Building, on_delete=models.CASCADE, related_name="travel_to"
    )
    travel_time_minutes = models.PositiveIntegerField()

    class Meta:
        unique_together = ("from_building", "to_building")
