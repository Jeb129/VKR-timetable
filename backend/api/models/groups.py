from django.db import models

from api.models.buildings import Building


class Institute(models.Model):
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=100)
    buildings_priority = models.ManyToManyField(Building, through="BuildingPriority", related_name="institutes_priority")

    def __str__(self):
        return self.short_name

class StudyProgram(models.Model):
    institute = models.ForeignKey(Institute, on_delete=models.CASCADE, related_name="study_programs")
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=100)

    def __str__(self):
        return self.short_name

class StudyGroup(models.Model):
    admission_year = models.PositiveIntegerField()
    stud_program = models.ForeignKey(StudyProgram, on_delete=models.CASCADE)
    learning_form = models.CharField(max_length=20)
    learning_stage = models.CharField(max_length=20)
    group_num = models.PositiveIntegerField()
    sub_groups = models.ManyToManyField('self', symmetrical=True, blank=True)
    sub_group_num = models.PositiveIntegerField()
    name = models.CharField(max_length=50)
    students_count = models.PositiveIntegerField()

    def __str__(self):
        return self.name