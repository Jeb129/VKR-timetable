from django.db import models

from api.models.buildings import Classroom
from api.models.education_subjects import Discipline, LessonType, StudyGroup, Teacher
from api.models.schedule import Semester, Timeslot


class Lesson(models.Model):
    """Финальное расписание (Таблица ключей)"""

    scenario = models.ForeignKey(
        "ScheduleScenario",
        on_delete=models.CASCADE,
        related_name="lessons",
        verbose_name="сценарий",
    )
    discipline = models.ForeignKey(
        Discipline, on_delete=models.CASCADE, verbose_name="дисциплина"
    )
    lesson_type = models.ForeignKey(
        LessonType, on_delete=models.CASCADE, verbose_name="вид занятия"
    )
    timeslot = models.ForeignKey(
        Timeslot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="слот расписания",
    )
    classroom = models.ForeignKey(
        Classroom, on_delete=models.CASCADE, verbose_name="аудитория"
    )
    teachers = models.ManyToManyField(Teacher, verbose_name="преподаватели")

    study_groups = models.ManyToManyField(StudyGroup, verbose_name="группы")
    whole_weeks = models.PositiveIntegerField(
        null=True, verbose_name="количество недель"
    )
    priority = models.SmallIntegerField(null=False,blank=True,default=0,verbose_name="Приоритет")

    class Meta:
        verbose_name = "занятие"
        verbose_name_plural = "занятия"

    def __str__(self) -> str:
        return f"{self.lesson_type} {self.discipline} ({self.timeslot})"


class AcademicLoad(models.Model):
    """Объединенная модель нагрузки (задание для генератора)"""

    # Семестр привязывает академическую нагрузку к конкретному временному промежутку
    merge_key = models.CharField(null=True, verbose_name="ключ связи")
    semester = models.ForeignKey(
        Semester, on_delete=models.SET_NULL, null=True, verbose_name="семестр"
    )
    discipline = models.ForeignKey(
        Discipline, on_delete=models.CASCADE, verbose_name="дисциплина"
    )
    lesson_type = models.ForeignKey(
        LessonType, on_delete=models.CASCADE, verbose_name="вид занятия"
    )
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name="loads",
        verbose_name="преподаватель",
    )
    study_group = models.ForeignKey(
        StudyGroup,
        on_delete=models.CASCADE,
        related_name="loads",
        verbose_name="группа",
    )
    control_type = models.CharField(
        null=True, max_length=20, verbose_name="вид контроля"
    )
    whole_hours = models.PositiveIntegerField(verbose_name="всего часов")
    whole_weeks = models.PositiveIntegerField(verbose_name="всего недель")

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

        return sem_year * 2 - sem_order + 1

    class Meta:
        verbose_name = "академическая нагрузка"
        verbose_name_plural = "академические нагрузки"

    def __str__(self):
        return f"{self.study_group} - {self.lesson_type} {self.discipline}"


class PlannedLesson(models.Model):
    """Агрегированное занятие, сформированное из AcademicLoad"""

    semester = models.ForeignKey(
        Semester, on_delete=models.CASCADE, verbose_name="семестр"
    )
    discipline = models.ForeignKey(
        Discipline, on_delete=models.CASCADE, verbose_name="дисциплина"
    )
    lesson_type = models.ForeignKey(
        LessonType, on_delete=models.CASCADE, verbose_name="вид занятия"
    )

    study_groups = models.ManyToManyField(StudyGroup, verbose_name="группы")
    teachers = models.ManyToManyField(Teacher, verbose_name="преподаватели")

    # источник данных
    academic_loads = models.ManyToManyField(AcademicLoad, verbose_name="источник")

    # рассчитанное количество занятий в 2 недели
    lessons_per_two_weeks = models.PositiveIntegerField(
        null=False,default=1, verbose_name="занятий за 2 недели"
    )
    whole_weeks = models.PositiveIntegerField(null=True, verbose_name="всего недель")
    priority = models.SmallIntegerField(null=False,blank=True,default=0,verbose_name="Приоритет")

    class Meta:
        verbose_name = "плановое занятие"
        verbose_name_plural = "плановые занятия"

    def __str__(self):
        return f"{self.lesson_type} {self.discipline}"
