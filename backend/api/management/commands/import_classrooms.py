import csv
import os
from datetime import time
from django.core.management.base import BaseCommand
from django.conf import settings 
from api.models.models import Classroom, Building

class Command(BaseCommand):
    help = 'Импорт аудиторий из CSV (колонки: eios_id, number)'
    file_path = os.path.join(settings.BASE_DIR, '..', 'api', 'classrooms.csv')

    def handle(self, *args, **options):
        with open(self.file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                eios_id = row['eios_id']
                number = row['number'] # Например "Б-201"
                
                # Автоматически определяем букву корпуса
                b_name = number.split('-')[0] if '-' in number else "Общий"
                building, _ = Building.objects.get_or_create(
                name=b_name,
                defaults={
                    'address': 'Уточняется',
                    'work_start_time': time(8, 0),
                    'work_end_time': time(20, 0)
                }
            )

                Classroom.objects.update_or_create(
                    eios_id=eios_id,
                    defaults={
                        'num': number,
                        'building': building,
                        'capacity': 30 # дефолт
                    }
                )
                count += 1
        self.stdout.write(self.style.SUCCESS(f"Импортировано {count} аудиторий"))