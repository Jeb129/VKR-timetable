import requests
from django.core.management.base import BaseCommand
from icalendar import Calendar
from datetime import datetime
from api.models.models import (
    Classroom, Lesson, ScheduleScenario, Discipline, 
    LessonType, Timeslot, Teacher
)

class Command(BaseCommand):
    help = 'Синхронизирует расписание из внешнего API EIOS'

    def handle(self, *args, **options):
        # 1. Получаем или создаем сценарий для импорта
        scenario, _ = ScheduleScenario.objects.get_or_create(
            name="EIOS Import",
            defaults={'is_active': False}
        )

        # Очищаем старые данные этого сценария перед обновлением
        Lesson.objects.filter(scenario=scenario).delete()

        # 2. Находим все аудитории, у которых прописан eios_id
        classrooms = Classroom.objects.exclude(eios_id__isnull=True)
        
        if not classrooms.exists():
            self.stdout.write(self.style.WARNING("Нет аудиторий с заполненным eios_id!"))
            return

        for room in classrooms:
            self.stdout.write(f"Синхронизация аудитории {room.num} (EIOS ID: {room.eios_id})...")
            
            try:
                url = f"https://eios.kosgos.ru/api/Rasp?idAudLine={room.eios_id}&iCal=true"
                response = requests.get(url, timeout=15)
                
                if not response.content:
                    continue

                cal = Calendar.from_ical(response.content)

                for component in cal.walk():
                    if component.name == "VEVENT":
                        summary = str(component.get('summary'))
                        dtstart = component.get('dtstart').dt
                        dtend = component.get('dtend').dt

                        # Парсим summary: "лаб Базы данных, п/г 2"
                        # Упрощенная логика: 
                        # - Тип занятия (первое слово до пробела)
                        # - Дисциплина (все остальное до запятой)
                        parts = summary.split(' ', 1)
                        type_str = parts[0] if len(parts) > 1 else "Занятие"
                        disc_str = parts[1].split(',')[0] if len(parts) > 1 else summary

                        # 3. Находим/Создаем дисциплину и тип
                        discipline, _ = Discipline.objects.get_or_create(name=disc_str)
                        lesson_type, _ = LessonType.objects.get_or_create(name=type_str)

                        # 4. Находим подходящий Timeslot по времени начала
                        # Важно: время в ICS обычно в UTC, переводим или сравниваем аккуратно
                        start_time = dtstart.time()
                        
                        # Ищем слот, который начинается в это же время
                        timeslot = Timeslot.objects.filter(
                            time_start__hour=start_time.hour,
                            time_start__minute=start_time.minute,
                            day=dtstart.weekday() + 1 # Пн=1 в нашей модели
                        ).first()

                        if not timeslot:
                            self.stdout.write(self.style.ERROR(f"Таймслот не найден для {start_time}"))
                            continue

                        # 5. Создаем занятие
                        lesson = Lesson.objects.create(
                            scenario=scenario,
                            discipline=discipline,
                            lesson_type=lesson_type,
                            timeslot=timeslot,
                            classroom=room
                        )
                        self.stdout.write(self.style.SUCCESS(f"  Добавлено: {disc_str}"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Ошибка при обработке {room.num}: {e}"))

        self.stdout.write(self.style.SUCCESS('Синхронизация завершена!'))