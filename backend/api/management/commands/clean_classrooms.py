import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from api.models import Classroom

class Command(BaseCommand):
    help = 'Экспорт уникальных аудиторий из БД в CSV (устранение дублей по названию)'

    def handle(self, *args, **options):
        # Путь к итоговому файлу
        output_path = os.path.join(os.path.dirname(settings.BASE_DIR), 'api', 'data', 'unique_classrooms.csv')
        
        # Обеспечим наличие папки data
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        self.stdout.write("Начинаю анализ дубликатов...")

        # Загружаем все аудитории из БД
        all_rooms = Classroom.objects.all().select_related('building')
        
        unique_map = {} # Название -> Объект
        
        for room in all_rooms:
            name = room.num.strip()
            # Если мы еще не встречали такую аудиторию или нашли ID поменьше (обычно основные ID меньше)
            if name not in unique_map:
                unique_map[name] = {
                    'eios_id': room.eios_id,
                    'number': name,
                    'building': room.building.name if room.building else 'Общий'
                }

        # Записываем в CSV
        with open(output_path, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['eios_id', 'number', 'building'])
            writer.writeheader()
            for entry in unique_map.values():
                writer.writerow(entry)

        self.stdout.write(self.style.SUCCESS(f"Экспорт завершен!"))
        self.stdout.write(f"Найдено уникальных аудиторий: {len(unique_map)} (из {all_rooms.count()} записей)")
        self.stdout.write(f"Файл сохранен здесь: {output_path}")