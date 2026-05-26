import os
import csv
from datetime import time
from django.core.management.base import BaseCommand
from django.conf import settings
from api.models import Building, Classroom

class Command(BaseCommand):
    help = "Импорт уникальных аудиторий из CSV в базу данных"

    def handle(self, *args, **options):
        # Путь к файлу. Убедитесь, что файл называется unique_classrooms.csv
        # и лежит в папке api/
        file_path = settings.DATA_FILES_DIR / "unique_classrooms.csv"

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"Файл не найден: {file_path}"))
            return

        self.stdout.write("Начинаю импорт...")
        # , encoding="utf-8"
        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                try:
                    eios_id = row.get("eios_id")
                    number = row.get("number")
                    b_code = row.get("building")

                    
                    if not eios_id or not number or not b_code:
                        continue

                    # 1. Получаем или создаем Корпус
                    building, _ = Building.objects.get_or_create(
                        short_name=b_code,
                        defaults={
                            "name": f"Корпус {b_code}",
                            "address": "Адрес не указан",
                            "work_start_time": time(8, 0),
                            "work_end_time": time(20, 0),
                        },
                    )

                    # 2. Создаем или обновляем Аудиторию
                    Classroom.objects.update_or_create(
                        eios_id=int(eios_id),
                        defaults={
                            "num": number,
                            "building": building,
                            "capacity": 30, # Дефолт
                        },
                    )
                    count += 1
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Ошибка в строке {row}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Успешно импортировано {count} уникальных аудиторий"))