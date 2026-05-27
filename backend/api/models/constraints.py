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
    weight = models.IntegerField(verbose_name="приоритет",help_text="Влияет на значение итоговой функции при генерации расписания")

    class Meta:
        ordering = ["institute", "building"]
        verbose_name = "приоритет корпусов"
        verbose_name_plural = "приоритеты корпусов"

    def __str__(self):
        return f"{self.institute} - {self.building} ({self.weight})"


class Constraint(models.Model):
    name = models.TextField(unique=True, verbose_name="имя метода")
    description = models.TextField(max_length=255, verbose_name="описание")
    weight = models.IntegerField(verbose_name="вес",help_text="Влияет на значение итоговой функции при генерации расписания")
    is_hard =models.BooleanField(default=False,
                                 verbose_name="запретить нарушения",
                                 help_text="Запрещает публикацию варианта расписания если есть хоть одно занятие, с нарушением такого ограничения")
    manual_only = models.BooleanField(default=False, 
                                          verbose_name="Исключить при генерации",
                                          help_text="При генерации расписания ограничение не будет учитываться")
    generation_only = models.BooleanField(default=False, 
                                          verbose_name="Исключить при ручных изменениях",
                                          help_text="Информация о нарушении ограничения не будет выводиться при ручном редактировании расписания")

    class Meta:
        verbose_name = "ограничение"
        verbose_name_plural = "ограничения"

    def __str__(self):
        return f"{self.description} ({self.name})"
