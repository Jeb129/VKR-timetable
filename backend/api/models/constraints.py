from django.db import models


from api.models.buildings import Equipment
from api.models.education_subjects import Institute, StudyGroup,Teacher, Discipline, LessonType, Building
from api.models.schedule import Semester


class EquipmentRequirement(models.Model):
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE)
    lesson_type = models.ForeignKey(LessonType, on_delete=models.CASCADE)
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)


class BuildingPriority(models.Model):
    institute = models.ForeignKey(Institute, on_delete=models.CASCADE)
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    weight = models.IntegerField()


class AcademicLoad(models.Model):
    """Объединенная модель нагрузки (задание для генератора)"""

    # Семестр привязывает академическую нагрузку к конкретному временному промежутку
    semester = models.ForeignKey(Semester, on_delete=models.SET_NULL, null=True)
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE)
    lesson_type = models.ForeignKey(LessonType, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name="loads")
    study_group = models.ForeignKey(
        StudyGroup, on_delete=models.CASCADE, related_name="loads"
    )
    whole_hours = models.PositiveIntegerField()
    whole_weeks = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.study_group} - {self.lesson_type} {self.discipline}"


class Constraint(models.Model):
    name = models.TextField(unique=True)
    description = models.TextField(max_length=255)
    weight = models.IntegerField()
