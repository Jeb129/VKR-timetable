# тут храняться модели которые мы делаем

from django.db import models
from authentification.models import CustomUser
from . import enums

# ---  АУДИТОРИИ И ИНФРАСТРУКТУРА ---

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
    building = models.ForeignKey(Building, on_delete=models.SET_NULL, related_name="classrooms", null=True, blank=True)
    num = models.CharField(max_length=20)
    name = models.CharField(max_length=100, blank=True)
    capacity = models.PositiveIntegerField()
    eios_id = models.IntegerField(null=True, blank=True, unique=True, help_text="ID аудитории в системе EIOS")
    equipment = models.ManyToManyField('Equipment', blank=True, related_name="classrooms")

    def __str__(self):
        if self.building is None:
            return self.name
        return f"{self.building.short_name} - {self.num}"

class BuildingTravelTime(models.Model):
    from_building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name="travel_from")
    to_building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name="travel_to")
    travel_time_minutes = models.PositiveIntegerField()

    class Meta:
        unique_together = ('from_building', 'to_building')

# ---  УЧЕБНЫЕ ГРУППЫ ---

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

# ---  ГЕНЕРАЦИЯ И ПЛАНИРОВАНИЕ ---

class ScheduleScenario(models.Model):
    """Варианты расписания"""
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=False)
    total_penalty = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

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
    user = models.OneToOneField(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)

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

class AcademicLoad(models.Model):
    """Объединенная модель нагрузки (задание для генератора)"""
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE)
    lesson_type = models.ForeignKey(LessonType, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name="loads")
    study_group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE, related_name="loads")
    hours_per_week = models.PositiveIntegerField() # Сколько пар в неделю нужно поставить
    required_equipment = models.ManyToManyField(Equipment, blank=True)
    preferred_building = models.ForeignKey(Building, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.study_group} - {self.discipline}"

class Lesson(models.Model):
    """Финальное расписание (Таблица ключей)"""
    scenario = models.ForeignKey('ScheduleScenario', on_delete=models.CASCADE, related_name='lessons')
    academic_load = models.ForeignKey(AcademicLoad, on_delete=models.CASCADE, null=True, blank=True)
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE)
    lesson_type = models.ForeignKey(LessonType, on_delete=models.CASCADE)
    timeslot = models.ForeignKey(Timeslot, on_delete=models.SET_NULL, null=True, blank=True)
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    teachers = models.ManyToManyField(Teacher)
    study_groups = models.ManyToManyField(StudyGroup)

# ---  ОГРАНИЧЕНИЯ И ПРИОРИТЕТЫ ---

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

# ---  ЗАЯВКИ (REQUESTS) ---

class Request(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.IntegerField(
        choices=enums.RequestStatus.choices,
        default=enums.RequestStatus.ON_MODERATION,
        db_index=True
    )
    request_type = models.IntegerField(choices=enums.RequestType.choices, null=True)

class ExcludedTimeslot(Request):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    timeslot = models.ForeignKey(Timeslot, on_delete=models.CASCADE)
    
    def save(self, *args, **kwargs):
        self.request_type = enums.RequestType.ExcludedTimeslot
        super().save(*args, **kwargs)

class ClassroomPreference(Request):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE)
    lesson_type = models.ForeignKey(LessonType, on_delete=models.CASCADE)
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    
    def save(self, *args, **kwargs):
        self.request_type = enums.RequestType.ClassroomPreference
        super().save(*args, **kwargs)

class Booking(Request):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    date_start = models.DateTimeField()
    date_end = models.DateTimeField()

    def save(self, *args, **kwargs):
        self.request_type = enums.RequestType.Booking
        super().save(*args, **kwargs)

class ScheduleAdjustment(Request):
    date = models.DateField()
    timeslot = models.ForeignKey(Timeslot, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        self.request_type = enums.RequestType.ScheduleAdjustment
        super().save(*args, **kwargs)