import requests
import time
import re
import logging
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand

# Импорты согласно вашей структуре
from api.models import (
    Semester, 
    Lesson, 
    ScheduleScenario, 
    Timeslot, 
    Institute, 
    StudyProgram, 
    Discipline, 
    LessonType, 
    StudyGroup, 
    Teacher, 
    Classroom)

logger = logging.getLogger(__name__)

def parse_group_info(group_code):
    """Разбор шифра группы типа 24-ИСбо-1"""
    pattern = r"(\d{2})-([А-Яа-я]+)([бмса])([озо])-([\w\d]+)"
    match = re.search(pattern, group_code)
    if not match: return None
    year_short, prog_abbr, stage_char, form_char, num = match.groups()
    stages = {'б': 'Бакалавриат', 'м': 'Магистратура', 'с': 'Специалитет', 'а': 'Аспирантура'}
    forms = {'о': 'Очная', 'з': 'Заочная', 'в': 'Вечерняя'}
    return {
        'year': 2000 + int(year_short),
        'prog_code': prog_abbr.upper(),
        'stage': stages.get(stage_char, 'Бакалавриат'),
        'form': forms.get(form_char, 'Очная'),
        'group_num': num,
        'sub_group_num': int(re.search(r"п/г\s*(\d+)", group_code).group(1)) if "п/г" in group_code else None
    }

def normalize_teacher_name(name):
    """Удаление лишних пробелов в ФИО"""
    if not name: return name
    name = name.strip()
    name = re.sub(r'\.\s+(?=[А-Я])', '.', name)
    name = re.sub(r'\s+', ' ', name)
    return name

class Command(BaseCommand):
    help = 'Синхронизация расписания с автоматическим созданием семестра и защитой от None-полей'
        
    def handle(self, *args, **options):
        # 1. Авто-создание семестра и сценария
        import_dates = ["2026-03-30", "2026-04-06"]
        first_date_obj = datetime.strptime(import_dates[0], "%Y-%m-%d").date()
        
        semester, _ = Semester.objects.get_or_create(
            date_start__lte=first_date_obj, 
            date_end__gte=first_date_obj,
            defaults={
                'name': f"Семестр импорта {first_date_obj.year}", 
                'date_start': first_date_obj - timedelta(days=30), 
                'date_end': first_date_obj + timedelta(days=150)
            }
        )
        
        scenario, _ = ScheduleScenario.objects.get_or_create(
            name="EIOS Import", 
            defaults={'is_active': True, 'semester': semester}
        )
        
        # Если семестр изменился, обновляем привязку
        if scenario.semester != semester:
            scenario.semester = semester
            scenario.save()

        self.stdout.write(self.style.SUCCESS(f"Работаем в семестре: {semester.name}"))
        self.stdout.write(self.style.WARNING("Очистка старых данных сценария..."))
        Lesson.objects.filter(scenario=scenario).delete()

        inst, _ = Institute.objects.get_or_create(name="Импорт", short_name="ИМП")
        rooms = Classroom.objects.exclude(eios_id__isnull=True)
        total_rooms = rooms.count()
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json'
        }

        room_counter = 0
        for room in rooms:
            room_counter += 1
            if room_counter % 30 == 0:
                self.stdout.write(self.style.MIGRATE_LABEL(f"Прогресс: {room_counter}/{total_rooms}. Ожидание 45 сек..."))
                time.sleep(45)

            for sdate in import_dates:
                url = f"https://eios.kosgos.ru/api/Rasp?idAudLine={room.eios_id}&sdate={sdate}"
                self.stdout.write(f"Запрос {room.num} [{sdate}]...")
                
                success = False
                for attempt in range(4):
                    try:
                        time.sleep(2.0) # Задержка для предотвращения бана
                        res = requests.get(url, headers=headers, timeout=20)
                        
                        if res.status_code == 429:
                            time.sleep(20)
                            continue
                        if res.status_code != 200:
                            continue

                        rasp_list = res.json().get('data', {}).get('rasp', [])
                        for item in rasp_list:
                            # Парсинг дисциплины и типа
                            disc_full = item.get('дисциплина', 'Неизвестно')
                            parts = disc_full.split(' ', 1)
                            type_abbr = parts[0].replace('.', '').strip()
                            discipline_name = parts[1].split(',')[0].strip() if len(parts) > 1 else disc_full

                            discipline, _ = Discipline.objects.get_or_create(name=discipline_name)
                            l_type, _ = LessonType.objects.get_or_create(name=type_abbr)

                            # ПРЕПОДАВАТЕЛЬ
                            teacher_fio = item.get('фиоПреподавателя')
                            teacher = None
                            if teacher_fio:
                                clean_name = normalize_teacher_name(teacher_fio)
                                teacher, _ = Teacher.objects.get_or_create(
                                    name=clean_name,
                                    defaults={
                                        'constraint_weight': 1, 
                                        'institute': inst,
                                        'max_hours_per_week': 36,
                                        'max_hours_per_day': 10
                                    }
                                )

                            # ГРУППА
                            group_name = item.get('группа')
                            group = None
                            if group_name and group_name != "Не указана":
                                # Сначала ищем по шифру (вдруг создана через Excel)
                                group = StudyGroup.objects.filter(name=group_name).first()
                                if not group:
                                    info = parse_group_info(group_name)
                                    if info:
                                        prog, _ = StudyProgram.objects.get_or_create(
                                            code=info['prog_code'][:8],
                                            defaults={'name': f"Программа {info['prog_code']}", 'institute': inst}
                                        )
                                        group = StudyGroup.objects.create(
                                            study_program=prog,
                                            admission_year=info['year'],
                                            group_num=info['group_num'],
                                            sub_group_num=info['sub_group_num'],
                                            learning_form=info['form'],
                                            learning_stage=info['stage'],
                                            students_count=25
                                        )

                            # ТАЙМСЛОТ
                            dt_obj = datetime.fromisoformat(item.get('дата').replace('Z', ''))
                            week_n = 1 if dt_obj.isocalendar()[1] % 2 != 0 else 2
                            slot = Timeslot.objects.filter(
                                day=item.get('деньНедели'), 
                                order_number=item.get('номерЗанятия'), 
                                week_num=week_n
                            ).first()

                            if slot:
                                #  добавлено whole_weeks для устранения ошибки в маппере
                                lesson, _ = Lesson.objects.get_or_create(
                                    scenario=scenario, 
                                    timeslot=slot, 
                                    classroom=room,
                                    discipline=discipline, 
                                    lesson_type=l_type,
                                    defaults={'whole_weeks': 18} # По умолчанию семестр
                                )
                                if teacher: lesson.teachers.add(teacher)
                                if group: lesson.study_groups.add(group)

                        self.stdout.write(self.style.SUCCESS(f"  [OK] {room.num} ({len(rasp_list)} пар)"))
                        success = True
                        break 
                        
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"  [ERR] {room.num}: {str(e)}"))
                        time.sleep(2)

        self.stdout.write(self.style.SUCCESS('\nСинхронизация завершена!'))