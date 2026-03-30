# тут храняться модели которые никуда логически не распределились

from django.db import models
from authentification.models import CustomUser



class Teacher(models.Model):
    name = models.CharField(max_length=255)
    weight = models.IntegerField()
    user = models.OneToOneField(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name