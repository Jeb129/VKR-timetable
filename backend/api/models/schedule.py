from django.db import models

from api.models.buildings import Classroom
from api.models.groups import StudyGroup
from api.models.models import Teacher

class Semester(models.Model):
    """Для отображения расписания в календаре"""
    name = models.CharField(max_length=255, unique=True)
    date_start = models.DateField(null=False,unique=True)
    date_end = models.DateField(null=False,unique=True)
    
    def __str__(self) -> str:
        return self.name

class ScheduleScenario(models.Model):
    """Варианты расписания"""
    name = models.CharField(max_length=255)
    semester = models.ForeignKey(Semester,on_delete=models.SET_NULL, null=True) # Для ограничения. Возможно сюр, но пока так
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
                name='unique_active_record'
            )
        ]

class Discipline(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class LessonType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Timeslot(models.Model):
    day = models.PositiveSmallIntegerField() # 1-6
    week_num = models.PositiveSmallIntegerField() # 1-2
    order_number = models.PositiveSmallIntegerField(default=1) # Номер пары
    time_start = models.TimeField()
    time_end = models.TimeField()

    def __str__(self):
        return f"День {self.day} | Пара {self.order_number}"



class Lesson(models.Model):
    """Финальное расписание (Таблица ключей)"""
    scenario = models.ForeignKey('ScheduleScenario', on_delete=models.CASCADE, related_name='lessons')
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE)
    lesson_type = models.ForeignKey(LessonType, on_delete=models.CASCADE)
    timeslot = models.ForeignKey(Timeslot, on_delete=models.SET_NULL, null=True, blank=True)
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    teachers = models.ManyToManyField(Teacher)

    # Ограничение: В одном занятии нельзя объединять несколько
    study_groups = models.ManyToManyField(StudyGroup)
