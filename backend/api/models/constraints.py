from django.db import models


from api.models.buildings import Equipment
from api.models.education_subjects import Institute, Discipline, LessonType, Building


class EquipmentRequirement(models.Model):
    discipline = models.ForeignKey(
        Discipline, on_delete=models.CASCADE, verbose_name="дисциплина"
    )
    lesson_type = models.ForeignKey(
        LessonType, on_delete=models.CASCADE, verbose_name="вид занятия"
    )
    equipment = models.ForeignKey(
        Equipment, on_delete=models.CASCADE, verbose_name="оборудование"
    )

    class Meta:
        verbose_name = "требование к оснащению аудитории"
        verbose_name_plural = "требования к оснащению аудиторий"

    def __str__(self):
        return f"{self.lesson_type.short_name} {self.discipline} - {self.equipment}"


class BuildingPriority(models.Model):
    institute = models.ForeignKey(
        Institute, on_delete=models.CASCADE, verbose_name="институт"
    )
    building = models.ForeignKey(
        Building, on_delete=models.CASCADE, verbose_name="клопус"
    )
    weight = models.IntegerField(verbose_name="приоритет")

    class Meta:
        ordering = ["institute", "building"]
        verbose_name = "приоритет корпусов"
        verbose_name_plural = "приоритеты корпусов"

    def __str__(self):
        return f"{self.institute} - {self.building} ({self.weight})"


class Constraint(models.Model):
    name = models.TextField(unique=True, verbose_name="имя метода")
    description = models.TextField(max_length=255, verbose_name="описание")
    weight = models.IntegerField(verbose_name="вес")

    class Meta:
        verbose_name = "ограничение"
        verbose_name_plural = "ограничения"

    def __str__(self):
        return f"{self.description} ({self.name})"
