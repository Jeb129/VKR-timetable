# Тут хранятся модели, которые имеют таблицы в БД

from django.db import models
from django.contrib.auth.models import User
import enums


# Аудитории

class Building(models.Model):
    '''
    Docstring for Building
    
    :var name: Буквенный код корпуса
    :vartype name: CharField[str]
    :var address: Адрес корпуса
    :vartype address: CharField[str]
    :var work_start_time: Начало рабочего дня
    :vartype work_start_time: TimeField[time]
    :var work_end_time: Конец рабочего дня
    :vartype work_end_time: TimeField[time]
    '''
    name = models.CharField(max_length=50)
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
        blank=True
    )
    num = models.CharField(max_length=20)
    name = models.CharField(max_length=100, blank=True)
    capacity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.name or self.num}"


# Учебные группы

class Institute(models.Model):
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=100)

    buildings_priority = models.ManyToManyField(
        Building,
        through= "BuildingPriority",
        related_name="institutes_priority",
    )

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
    sub_groups= models.ManyToManyField(
        'self',
        symmetrical=True,
        blank=True
    )
    sub_group_num = models.PositiveIntegerField()
    name = models.CharField(max_length=50)
    students_count = models.PositiveIntegerField()

    def __str__(self):
        return self.name


# Занятия

class Discipline(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class LessonType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Teacher(models.Model):
    name = models.CharField(max_length=255)
    weight = models.IntegerField()
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name

class Timeslot(models.Model):
    day = models.PositiveSmallIntegerField()
    week_num = models.PositiveSmallIntegerField()
    time_start = models.TimeField()
    time_end = models.TimeField()

    def __str__(self):
        return f"{self.day} / {self.time_start}-{self.time_end}"

class Lesson(models.Model):
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE)
    lesson_type = models.ForeignKey(LessonType, on_delete=models.CASCADE)
    timeslot = models.ForeignKey(
        Timeslot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.CASCADE
    )
    teachers = models.ManyToManyField(Teacher, blank=True)
    study_groups = models.ManyToManyField(StudyGroup, blank=True)

    def __str__(self):
        return f"{self.discipline} ({self.lesson_type})"


# Генерация

class EquipmentRequirement(models.Model):
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE)
    lesson_type = models.ForeignKey(LessonType, on_delete=models.CASCADE)
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)

class BuildingPriority(models.Model):
    institute = models.ForeignKey(Institute, on_delete=models.CASCADE)
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    weight = models.IntegerField()
    
class Constraint(models.Model):
    name = models.TextField()
    weight = models.IntegerField()   

# Определяет сколько часов дисциплины нужно провести для группы опредленным типом ( типо 22 ИСбо-1 матан парктика столько то часов)
class AcademicLoad(models.Model):
    study_group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE, related_name="loads")
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE)
    lesson_type = models.ForeignKey(LessonType, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    hours_per_week = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.study_group} - {self.discipline} ({self.lesson_type})"

# Заявки:

class Request(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.IntegerField(
        choices=enums.RequestStatus.choices,
        default=enums.RequestStatus.ON_MODERATION,
        db_index=True
    )

class ExcludedTimeslot(Request):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    timeslot = models.ForeignKey(Timeslot, on_delete=models.CASCADE)
    def save(self, *args, **kwargs):
        self.type = enums.RequestType.ExcludedTimeslot
        super().save(*args, **kwargs)

class ClassroomPreference(Request):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE)
    lesson_type = models.ForeignKey(LessonType, on_delete=models.CASCADE)
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    def save(self, *args, **kwargs):
        self.type = enums.RequestType.ClassroomPreference
        super().save(*args, **kwargs)

class Booking(Request):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    date_start = models.DateTimeField()
    date_end = models.DateTimeField()
    def save(self, *args, **kwargs):
        self.type = enums.RequestType.Booking
        super().save(*args, **kwargs)

class ScheduleAdjustment(Request):
    date = models.DateField()
    timeslot = models.ForeignKey(Timeslot, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        self.type = enums.RequestType.ScheduleAdjustment
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Adjustment {self.id}"

