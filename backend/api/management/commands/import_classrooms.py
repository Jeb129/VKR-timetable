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
        file_path = os.path.join(os.path.dirname(settings.BASE_DIR),"backend", "api", "unique_classrooms.csv")

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"Файл не найден: {file_path}"))
            return

        self.stdout.write("Начинаю импорт...")

        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                try:
                    eios_id = row.get("eios_id")
                    number = row.get("number")
                    
                    if not eios_id or not number:
                        continue

                    # Определяем код корпуса (например, 'Б' из 'Б-204')
                    b_code = number.split("-")[0] if "-" in number else "К"
                    b_code = b_code[:5] # Ограничение модели max_length=5

                    # 1. Получаем или создаем Корпус
                    building, _ = Building.objects.get_or_create(
                        short_name=b_code,
                        defaults={
                            "name": f"Корпус {b_code}",
                            "address": "ул. Университетская, д. 1", # Можно поправить позже
                            "work_start_time": time(8, 0),
                            "work_end_time": time(21, 0),
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