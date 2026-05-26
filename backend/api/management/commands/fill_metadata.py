from django.core.management.base import BaseCommand

# ИСПРАВЛЕННЫЕ ИМПОРТЫ: вытягиваем модели из новых файлов
from api.models import *
from api.services.data_import.default import init_default


class Command(BaseCommand):
    help = "Заполнение сетки времени и базовых ограничений"

    def handle(self, *args, **kwargs):
        self.stdout.write(
            self.style.SUCCESS(
                str(init_default())
            )
        )