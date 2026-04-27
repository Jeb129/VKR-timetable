from django.db import models

from authentification.models import CustomUser

from api.models.buildings import Building


class Institute(models.Model):
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=100)
    buildings_priority = models.ManyToManyField(
        Building, through="BuildingPriority", related_name="institutes_priority"
    )

    def __str__(self):
        return self.short_name


class StudyProgram(models.Model):
    institute = models.ForeignKey(
        Institute, on_delete=models.CASCADE, related_name="study_programs"
    )
    code = models.CharField(max_length=8, blank=False, unique=True, verbose_name="Шифр")
    name = models.CharField(
        max_length=255, blank=False, verbose_name="Наименование"
    )
    short_name = models.CharField(
        max_length=100, blank=True, verbose_name="Сокращение"
    )

    class Meta:
        verbose_name = "направление подготовки"
        verbose_name_plural = "направления подготовки"

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        if not self.short_name:
            self.short_name = "".join(
                [w[0] for w in self.name.upper().split(maxsplit=1)]
            )
        super().save(*args, **kwargs)


class Discipline(models.Model):
    name = models.CharField(max_length=255)
    allow_merge_teachers = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class LessonType(models.Model):
    name = models.CharField(max_length=50)
    short_name = models.CharField(max_length=20,blank=True,null=True)
    allow_merge_teachers = models.BooleanField(default=False)
    allow_merge_subgroups = models.BooleanField(default=False)
    allow_merge_groups = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class StudyGroup(models.Model):
    admission_year = models.PositiveIntegerField(verbose_name="Год поступления")
    study_program = models.ForeignKey(
        StudyProgram, on_delete=models.CASCADE, verbose_name="Направление подготовки"
    )
    learning_form = models.CharField(max_length=20, verbose_name="Форма обучения")
    learning_stage = models.CharField(max_length=20, verbose_name="Уровень подготовки")
    group_num = models.CharField(max_length=5, verbose_name="Номер группы")
    sub_groups = models.ManyToManyField("self", symmetrical=True, blank=True)
    sub_group_num = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Номер подгруппы"
    )
    name = models.CharField(max_length=50, verbose_name="Шифр")
    students_count = models.PositiveIntegerField(verbose_name="Количество студентов")

    class Meta:
        ordering = ["admission_year"]
        verbose_name = "учебная группа"
        verbose_name_plural = "учебные группы"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = f"{str(self.admission_year)[-2:]}-{self.study_program.short_name}{self.learning_stage.lower()[0]}{self.learning_form.lower()[0]}-{self.group_num}{f" п/г {self.sub_group_num}" if self.sub_group_num else ""}"
        super().save(*args, **kwargs)


class Teacher(models.Model):
    institute = models.ForeignKey(
        Institute,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name="Институт",
    )
    name = models.CharField(max_length=255, verbose_name="ФИО")
    post = models.CharField(max_length=30,null=True, blank=True, verbose_name="Должность")
    constraint_weight = models.IntegerField(
        default=1, verbose_name="Коэффицент приоритета ограничений"
    )
    user = models.OneToOneField(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["name","institute"]
        verbose_name = "преподаватель"
        verbose_name_plural = "преподаватели"

    def __str__(self):
        return self.name
