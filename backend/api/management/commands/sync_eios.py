import requests
import logging
import time 
import pytz
from datetime import datetime 
from django.utils import timezone
from django.core.management.base import BaseCommand
from icalendar import Calendar
from api.models import *

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Универсальный импорт расписания из EIOS'

    def handle(self, *args, **options):
        # 1. Сценарий
        scenario, _ = ScheduleScenario.objects.get_or_create(
            name="EIOS Import", 
            defaults={'is_active': True}
        )
        Lesson.objects.filter(scenario=scenario).delete()

        
        moscow_tz = pytz.timezone('Europe/Moscow')

        rooms = Classroom.objects.exclude(eios_id__isnull=True)
        
        self.stdout.write(f"Начинаю синхронизацию {rooms.count()} аудиторий...")

        for room in rooms:
            url = f"https://eios.kosgos.ru/api/Rasp?idAudLine={room.eios_id}&iCal=true"
            
            success = False
            max_retries = 3  # Количество попыток для одной аудитории
            
            for attempt in range(max_retries):
                try:
                 # Пауза 2 секунды перед каждым запросом, чтобы сервер не забанил
                    time.sleep(2) 
                    
                    res = requests.get(url, timeout=15)
                    
                    if res.status_code == 429:
                        wait_time = (attempt + 1) * 10 # С каждой ошибкой ждем дольше (10, 20с)
                        self.stdout.write(self.style.ERROR(f"Бан (429) для {room.num}. Попытка {attempt+1}. Ждем {wait_time}с..."))
                        time.sleep(wait_time)
                        continue # Пробуем еще раз эту же аудиторию

                    if not res.content or b"BEGIN:VCALENDAR" not in res.content:
                        self.stdout.write(self.style.WARNING(f"Пустое расписание или ошибка для {room.num}"))
                        continue
                    
                    cal = Calendar.from_ical(res.content)
                    for event in cal.walk('VEVENT'):
                        summary = str(event.get('summary'))
                        dtstart = event.get('dtstart').dt
                        
                        if isinstance(dtstart, datetime):
                            # Конвертируем UTC -> Moscow
                            moscow_tz = pytz.timezone('Europe/Moscow')
                            # Если время в UTC (имеет таймзону), переводим в Москву
                            if dtstart.tzinfo:
                                dtstart = dtstart.astimezone(moscow_tz)
                            start_t = dtstart.time()
                        else:
                            # Если это просто дата (целый день), берем дефолтное время
                            start_t = datetime.combine(dtstart, datetime.min.time()).time()
                        
                        # Парсинг строки: "пр. Иностранный язык, ..."
                        parts = summary.split(' ', 1)
                        type_abbr = parts[0].replace('.', '').strip() # 'пр', 'лек', 'лаб'
                        content = parts[1] if len(parts) > 1 else ""
                        disc_name = content.split(',')[0].strip()

                        # АВТО-СОЗДАНИЕ ДАННЫХ (вместо пропуска)
                        discipline, _ = Discipline.objects.get_or_create(name=disc_name)
                        l_type, _ = LessonType.objects.get_or_create(name=type_abbr)
                        
                        # Поиск таймслота
                        slot = Timeslot.objects.filter(
                            day=dtstart.weekday() + 1,
                            time_start__hour=start_t.hour,
                            time_start__minute=start_t.minute
                        ).first()

                        if slot:
                            # Используем get_or_create, чтобы не плодить одинаковые записи в одном кабинете
                            lesson, created = Lesson.objects.get_or_create(
                                scenario=scenario,
                                timeslot=slot,
                                classroom=room,
                                defaults={
                                    'discipline': discipline,
                                    'lesson_type': l_type,
                                }
                            )
                            if created:
                                self.stdout.write(self.style.SUCCESS(f"  + {room.num}: {disc_name}"))
                            else:
                                # Если занятие уже есть (например, для другой подгруппы), 
                                # мы просто не создаем дубликат
                                self.stdout.write(self.style.WARNING(f"  ~ {room.num}: {disc_name} (уже существует)"))
                    success = True
                    break
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Ошибка в {room.num}: {e}"))
                    time.sleep(5)
            if not success:
                self.stdout.write(self.style.ERROR(f"!!! Не удалось загрузить {room.num} после {max_retries} попыток"))