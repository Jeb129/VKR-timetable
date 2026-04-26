import requests
import time
import random
from django.core.management.base import BaseCommand
from api.models import Building, Classroom
from datetime import time as dt_time

class Command(BaseCommand):
    help = 'Перебор ID для поиска всех аудиторий в EIOS'

    def handle(self, *args, **options):
        # Конфигурация диапазонов
        RANGES = [
            (3566000, 3620000), # Основной массив
        ]
        ARTIFACTS = [5007733] # Известные разовые ID
        
        # Объединяем всё в один итератор
        total_to_check = sum(r[1] - r[0] for r in RANGES) + len(ARTIFACTS)
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }

        self.stdout.write(self.style.MIGRATE_LABEL(f"Начинаю поиск. Всего ID для проверки: {total_to_check}"))
        
        found_count = 0
        checked_count = 0

        # Функция для проверки одного ID
        def check_id(eios_id):
            nonlocal found_count, checked_count
            url = f"https://eios.kosgos.ru/api/Rasp?idAudLine={eios_id}"
            
            try:
                # Маленькая пауза для стабильности
                time.sleep(0.05) 
                
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 429:
                    self.stdout.write(self.style.ERROR("\n[!] Лимит превышен. Спим 30 секунд..."))
                    time.sleep(30)
                    return

                if response.status_code == 200:
                    data = response.json()
                    # Ищем название аудитории в блоке info -> aud -> name
                    aud_info = data.get('data', {}).get('info', {}).get('aud', {})
                    full_name = aud_info.get('name')

                    if full_name and full_name.strip():
                        # Мы нашли живую аудиторию!
                        self.save_classroom(eios_id, full_name.strip())
                        found_count += 1
                        self.stdout.write(self.style.SUCCESS(f"\n[+] Найдена: {full_name} (ID: {eios_id})"))

            except Exception as e:
                pass # Пропускаем сетевые ошибки
            
            checked_count += 1
            if checked_count % 100 == 0:
                # Печатаем прогресс в той же строке
                self.stdout.write(f"\rПрогресс: {checked_count}/{total_to_check} ID проверено... Найдено: {found_count}", ending='')

        # Запуск перебора
        for start, end in RANGES:
            for current_id in range(start, end + 1):
                check_id(current_id)
        
        for art_id in ARTIFACTS:
            check_id(art_id)

        self.stdout.write(self.style.SUCCESS(f"\n\nПоиск завершен! Итого найдено: {found_count} аудиторий."))

    def save_classroom(self, eios_id, full_name):
        """Логика создания/обновления в БД"""
        b_prefix = full_name.split('-')[0] if '-' in full_name else 'Общий'
        
        building, _ = Building.objects.get_or_create(
            short_name=b_prefix[:5],
            defaults={
                'name': f"Корпус {b_prefix}",
                'address': 'Автоматический импорт',
                'work_start_time': dt_time(8, 0),
                'work_end_time': dt_time(21, 0)
            }
        )

        Classroom.objects.update_or_create(
            eios_id=eios_id,
            defaults={
                'num': full_name,
                'building': building,
                'capacity': 30
            }
        )