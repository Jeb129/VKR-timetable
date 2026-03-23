import requests
from django.core.management.base import BaseCommand
from icalendar import Calendar
from datetime import datetime
from api.models.models import (
    Classroom, Lesson, ScheduleScenario, Discipline, 
    LessonType, Timeslot, Teacher, StudyGroup
)

class Command(BaseCommand):
    help = 'Синхронизирует расписание из EIOS в базу данных'

    def handle(self, *args, **options):
        # 1. Получаем/создаем сценарий импорта
        scenario, _ = ScheduleScenario.objects.get_or_create(
            name="EIOS Import",
            defaults={'is_active': True}
        )

        # Очищаем старые данные этого сценария
        Lesson.objects.filter(scenario=scenario).delete()

        # 2. Ищем аудитории с заполненным eios_id
        classrooms = Classroom.objects.exclude(eios_id__isnull=True)
        
        for room in classrooms:
            self.stdout.write(f"Обработка аудитории: {room.num} (EIOS ID: {room.eios_id})")
            url = f"https://eios.kosgos.ru/api/Rasp?idAudLine={room.eios_id}&iCal=true"
            
            try:
                response = requests.get(url, timeout=15)
                if not response.content: continue
                
                cal = Calendar.from_ical(response.content)
                for component in cal.walk('VEVENT'):
                    summary = str(component.get('summary'))
                    dtstart = component.get('dtstart').dt
                    
                    # Парсинг строки "лаб Базы данных, п/г 1, Иванов И.И."
                    # Логика: Тип - до первого пробела, Дисциплина - до запятой
                    parts = summary.split(' ', 1)
                    type_name = parts[0] if len(parts) > 1 else "Занятие"
                    rest = parts[1] if len(parts) > 1 else summary
                    discipline_name = rest.split(',')[0]

                    discipline, _ = Discipline.objects.get_or_create(name=discipline_name)
                    l_type, _ = LessonType.objects.get_or_create(name=type_name)

                    # Поиск таймслота (Пн=0 в ical, Пн=1 в твоей модели)
                    start_time = dtstart.time()
                    timeslot = Timeslot.objects.filter(
                        day=dtstart.weekday() + 1,
                        time_start__hour=start_time.hour,
                        time_start__minute=start_time.minute
                    ).first()

                    if timeslot:
                        lesson = Lesson.objects.create(
                            scenario=scenario,
                            discipline=discipline,
                            lesson_type=l_type,
                            timeslot=timeslot,
                            classroom=room
                        )
                        # Если в строке есть фамилия, можно попробовать найти Teacher
                        self.stdout.write(self.style.SUCCESS(f"  + {discipline_name}"))
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Ошибка {room.num}: {e}"))