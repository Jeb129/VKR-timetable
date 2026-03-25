import requests
import logging
from django.core.management.base import BaseCommand
from icalendar import Calendar
from api.models.models import *

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Универсальный импорт расписания из EIOS'

    def handle(self, *args, **options):
        # 1. Получаем активный сценарий импорта
        scenario, _ = ScheduleScenario.objects.get_or_create(name="EIOS Import")
        Lesson.objects.filter(scenario=scenario).delete()

        rooms = Classroom.objects.exclude(eios_id__isnull=True)
        
        for room in rooms:
            url = f"https://eios.kosgos.ru/api/Rasp?idAudLine={room.eios_id}&iCal=true"
            try:
                res = requests.get(url, timeout=10)
                if not res.content: continue
                
                cal = Calendar.from_ical(res.content)
                for event in cal.walk('VEVENT'):
                    summary = str(event.get('summary')) # "лек Высшая математика, Иванов И.И., ПИН-23"
                    dtstart = event.get('dtstart').dt
                    
                    # Парсинг строки
                    parts = summary.split(' ', 1)
                    type_name = parts[0]
                    content = parts[1] if len(parts) > 1 else ""
                    
                    # Извлекаем дисциплину (до первой запятой)
                    disc_name = content.split(',')[0].strip()
                    
                    # Пытаемся найти метаданные. Если нет - логгируем ошибку
                    try:
                        discipline = Discipline.objects.get(name=disc_name)
                        l_type = LessonType.objects.get(name__icontains=type_name)
                        
                        # Ищем таймслот
                        start_t = dtstart.time()
                        slot = Timeslot.objects.filter(
                            day=dtstart.weekday() + 1,
                            time_start__hour=start_t.hour,
                            time_start__minute=start_t.minute
                        ).first()

                        if not slot:
                            logger.error(f"Таймслот не найден: {dtstart}")
                            continue

                        # Создаем занятие (только расписание)
                        Lesson.objects.create(
                            scenario=scenario,
                            discipline=discipline,
                            lesson_type=l_type,
                            timeslot=slot,
                            classroom=room
                        )

                    except (Discipline.DoesNotExist, LessonType.DoesNotExist) as e:
                        # Логгируем, но не падаем. Это и есть "выбрасываем ошибку в логи"
                        logger.warning(f"Пропущено занятие '{disc_name}': данных нет в справочниках БД")
                        
            except Exception as e:
                logger.error(f"Критическая ошибка при синхронизации {room.num}: {e}")