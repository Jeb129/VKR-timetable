from django.contrib.auth.models import AbstractUser
from django.db import models

from api.models import Teacher, StudyGroup


class CustomUser(AbstractUser):
    username = models.CharField(max_length=150, blank=True, null=True, unique=False, verbose_name="Логин")
    # переопределяем email → делаем уникальным
    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"
    internal_user =  models.BooleanField(default=False,  null=False, blank=True, verbose_name="Внутренний пользователь")
    is_email_verified =  models.BooleanField(default=False,  null=False, blank=True, verbose_name="Подтвержденный email")
    is_schedule_moderator =  models.BooleanField(default=False,  null=False, blank=True, verbose_name="Модератор расписания")
    is_booking_moderator =  models.BooleanField(default=False,  null=False, blank=True, verbose_name="Модератор бронирования")

    # PDN_allow =  models.BooleanField(default=False,  null=False, blank=True, verbose_name="Пользователь дал согласие на обработку ПДн")

    moodle_id = models.IntegerField(null=True, blank=True, verbose_name="ID в Moodle")

    teacher = models.ForeignKey("api.Teacher", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Связанный преподаватель")
    study_group = models.ForeignKey("api.StudyGroup", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Связанная учебная группа")

    REQUIRED_FIELDS = ["username"]

    @property
    def is_internal(self):
        # Пользователь считается внутренним, если флаг установлен вручную 
        # ИЛИ если он успешно привязал Moodle
        return self.internal_user or self.moodle_id is not None

    def __str__(self):
        return self.email