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


class Constraint(models.Model):
    name = models.TextField(unique=True)
    description = models.TextField(max_length=255)
    weight = models.IntegerField()
