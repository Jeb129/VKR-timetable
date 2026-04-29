from django.db import models

from api.models.buildings import Classroom
from api.models.education_subjects import Discipline, LessonType, StudyGroup, Teacher
from api.models.schedule import Semester, Timeslot

class Lesson(models.Model):
    """Финальное расписание (Таблица ключей)"""

    scenario = models.ForeignKey(
        "ScheduleScenario", on_delete=models.CASCADE, related_name="lessons"
    )
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE)
    lesson_type = models.ForeignKey(LessonType, on_delete=models.CASCADE)
    timeslot = models.ForeignKey(
        Timeslot, on_delete=models.SET_NULL, null=True, blank=True
    )
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    teachers = models.ManyToManyField(Teacher)

    # Ограничение: В одном занятии нельзя объединять несколько
    study_groups = models.ManyToManyField(StudyGroup)

    def __str__(self) -> str:
        return f"{self.lesson_type} {self.discipline}"
    
class AcademicLoad(models.Model):
    """Объединенная модель нагрузки (задание для генератора)"""

    # Семестр привязывает академическую нагрузку к конкретному временному промежутку
    merge_key = models.CharField(null=True)
    semester = models.ForeignKey(Semester, on_delete=models.SET_NULL, null=True)
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE)
    lesson_type = models.ForeignKey(LessonType, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name="loads")
    study_group = models.ForeignKey(
        StudyGroup, on_delete=models.CASCADE, related_name="loads"
    )
    control_type = models.CharField(null=True,max_length=20)
    whole_hours = models.PositiveIntegerField()
    whole_weeks = models.PositiveIntegerField()

    @property
    def semester_order(self):
        sem_order = 1 if self.semester.date_start.month < 7 else 0
        sem_year = self.semester.date_start.year - self.study_group.admission_year

        # Расчет семестра Осень 2022 для 22-ИСбо-1
        # sem_order = 0 (сентябрь 9 месяц)
        # sem_year = 2022 - 2022  = 0
        # sem = 0 * 2 - 0 + 1 = 1

        # Расчет семестра Весна 2023 для 22-ИСбо-1
        # sem_order = 1 (январь 1 месяц)
        # sem_year = 2023 - 2022  = 1
        # sem = 1 * 2 - 1 + 1 = 8

        # Расчет семестра Осень 2025 для 22-ИСбо-1
        # sem_order = 0 (сентябрь 9 месяц)
        # sem_year = 2025 - 2022  = 3
        # sem = 3 * 2 - 0 + 1 = 7

        # Расчет семестра Весна 2026 для 22-ИСбо-1
        # sem_order = 1 (январь 1 месяц)
        # sem_year = 2026 - 2022  = 4
        # sem = 4 * 2 - 1 + 1 = 8
        
        return sem_year*2 - sem_order + 1

    def __str__(self):
        return f"{self.study_group} - {self.lesson_type} {self.discipline}"

class PlannedLesson(models.Model):
    """Агрегированное занятие, сформированное из AcademicLoad"""

    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE)
    lesson_type = models.ForeignKey(LessonType, on_delete=models.CASCADE)

    study_groups = models.ManyToManyField(StudyGroup)
    teachers = models.ManyToManyField(Teacher)

    # источник данных
    academic_loads = models.ManyToManyField(AcademicLoad)

    # рассчитанное количество занятий в 2 недели
    lessons_count = models.PositiveIntegerField() 

    class Meta:
        verbose_name = "плановое занятие"
        verbose_name_plural = "плановые занятия"

    def __str__(self):
        return f"{self.lesson_type} {self.discipline}"