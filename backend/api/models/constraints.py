from django.db import models

from api.models.buildings import Building, Equipment
from api.models.groups import Institute, StudyGroup
from api.models.models import Teacher
from api.models.schedule import Discipline, LessonType

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
    semester = models.PositiveSmallIntegerField(null=False)
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE)
    lesson_type = models.ForeignKey(LessonType, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name="loads")
    study_group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE, related_name="loads")
    hours_per_week = models.PositiveIntegerField() # Сколько пар в неделю нужно поставить
    
    def __str__(self):
        return f"{self.study_group} - {self.discipline}"
    
class Constraint(models.Model):
    name = models.TextField(unique=True)
    description = models.TextField(max_length=255)
    weight = models.IntegerField()   