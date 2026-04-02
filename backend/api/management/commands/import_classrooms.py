import os
import csv
from datetime import time
from django.core.management.base import BaseCommand
from django.conf import settings

from api.models import Building, Classroom


class Command(BaseCommand):
    help = "Импорт аудиторий из CSV"

    def handle(self, *args, **options):
        # Путь к файлу (с учетом config)
        file_path = settings.BASE_DIR / "api/classrooms.csv"

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"Файл не найден по пути: {file_path}"))
            return

        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                eios_id = row["eios_id"]
                number = row["number"]

                b_name = number.split("-")[0] if "-" in number else "Общий"

                # Теперь указываем short_name, так как оно обязательно в новой модели
                building, _ = Building.objects.get_or_create(
                    name=b_name,
                    defaults={
                        "short_name": b_name[
                            :5
                        ],  # Берем первые 5 символов (ограничение модели)
                        "address": "Уточняется",
                        "work_start_time": time(8, 0),
                        "work_end_time": time(21, 0),
                    },
                )

                Classroom.objects.update_or_create(
                    eios_id=eios_id,
                    defaults={
                        "num": number,
                        "building": building,
                        "capacity": 30,
                    },
                )
                count += 1
        self.stdout.write(self.style.SUCCESS(f"Импортировано {count} аудиторий"))
