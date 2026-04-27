from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.

class CustomUser(AbstractUser):
    username = models.CharField(max_length=150, blank=True, null=True, unique=False)
    # переопределяем email → делаем уникальным
    email = models.EmailField(unique=True)

    # Django будет использовать email как логин
    USERNAME_FIELD = "email"
    internal_user =  models.BooleanField(default=False,  null=False, blank=True)
    is_email_verified =  models.BooleanField(default=False,  null=False, blank=True)
    is_schedule_moderator =  models.BooleanField(default=False,  null=False, blank=True)
    is_booking_moderator =  models.BooleanField(default=False,  null=False, blank=True)

    # ID из moodle которое вытягивается при подтверждении аккаунта
    moodle_id = models.IntegerField(null=True, blank=True, verbose_name="ID в Moodle")

    # Поля, которые будут спрашивать при создании суперпользователя
    # username остается, но он не используется как логин
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.email