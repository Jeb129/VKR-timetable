import requests
import time
import re
import logging
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from api.models import (
    Semester, 
    ScheduleScenario, 
    Timeslot,
    Lesson, 
    Institute, 
    StudyProgram, 
    Discipline, 
    LessonType, 
    StudyGroup, 
    Teacher,
    Classroom)

logger = logging.getLogger(__name__)

def parse_group_info(group_code):
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
    if not name:
        return name
    # Убираем лишние пробелы по краям
    name = name.strip()
    #  Убираем пробелы между инициалами 
    name = re.sub(r'\.\s+(?=[А-Я])', '.', name)
    # Заменяем множественные пробелы на один
    name = re.sub(r'\s+', ' ', name)
    return name

class Command(BaseCommand):
    help = 'Синхронизация расписания с защитой от блокировок и умным поиском данных'
        
    def handle(self, *args, **options):
        # 1. Подготовка семестра и сценария
        import_dates = ["2026-03-30", "2026-04-06"]
        first_date = datetime.strptime(import_dates[0], "%Y-%m-%d").date()
        
        semester, _ = Semester.objects.get_or_create(
            date_start__lte=first_date, date_end__gte=first_date,
            defaults={'name': f"Семестр {first_date.year}", 'date_start': first_date - timedelta(days=30), 'date_end': first_date + timedelta(days=120)}
        )
        scenario, _ = ScheduleScenario.objects.get_or_create(
            name="EIOS Import", defaults={'is_active': True, 'semester': semester}
        )
        
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
                self.stdout.write(self.style.MIGRATE_LABEL(f"Прогресс: {room_counter}/{total_rooms}. Ожидание 60 сек..."))
                time.sleep(60)

            for sdate in import_dates:
                url = f"https://eios.kosgos.ru/api/Rasp?idAudLine={room.eios_id}&sdate={sdate}"
                self.stdout.write(f"Запрос {room.num} [{sdate}]...")
                
                success = False
                for attempt in range(4): # 4 попытки на каждую ссылку
                    try:
                        time.sleep(2.5) # Увеличенная пауза между запросами
                        res = requests.get(url, headers=headers, timeout=25)
                        
                        if res.status_code == 429:
                            self.stdout.write(self.style.ERROR(f"  [!] Бан 429. Ждем 30с..."))
                            time.sleep(30)
                            continue
                            
                        if res.status_code != 200:
                            time.sleep(5)
                            continue

                        rasp_list = res.json().get('data', {}).get('rasp', [])
                        for item in rasp_list:
                            # Парсинг дисциплины
                            disc_full = item.get('дисциплина', 'Неизвестно')
                            parts = disc_full.split(' ', 1)
                            type_abbr = parts[0].replace('.', '').strip()
                            discipline_name = parts[1].split(',')[0].strip() if len(parts) > 1 else disc_full

                            discipline, _ = Discipline.objects.get_or_create(name=discipline_name)
                            l_type, _ = LessonType.objects.get_or_create(name=type_abbr)

                            # ПРЕПОДАВАТЕЛЬ: Сначала ищем (мог быть из Excel)
                            teacher_fio = item.get('фиоПреподавателя')
                            teacher = None
                            if teacher_fio:
                                clean_name = normalize_teacher_name(teacher_fio)
        
                                teacher, created = Teacher.objects.get_or_create(
                                    name=clean_name, # Ищем по чистому имени
                                    defaults={'constraint_weight': 1, 'institute': inst}
                                )
                                if not teacher:
                                    teacher = Teacher.objects.create(name=teacher_fio, constraint_weight=1, institute=inst)

                            # ГРУППА: Сначала ищем
                            group_name = item.get('группа')
                            group = None
                            if group_name and group_name != "Не указана":
                                # Пытаемся найти уже существующую группу по имени (шифру)
                                group = StudyGroup.objects.filter(name=group_name).first()
                                if not group:
                                    info = parse_group_info(group_name)
                                    if info:
                                        prog, _ = StudyProgram.objects.get_or_create(
                                            code=info['prog_code'][:8],
                                            defaults={'name': f"Направление {info['prog_code']}", 'institute': inst}
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
                            slot = Timeslot.objects.filter(day=item.get('деньНедели'), order_number=item.get('номерЗанятия'), week_num=week_n).first()

                            if slot:
                                # Создаем ПАРУ (т.к. их нет в Excel)
                                lesson, _ = Lesson.objects.get_or_create(
                                    scenario=scenario, timeslot=slot, classroom=room,
                                    discipline=discipline, lesson_type=l_type
                                )
                                if teacher: lesson.teachers.add(teacher)
                                if group: lesson.study_groups.add(group)

                        self.stdout.write(self.style.SUCCESS(f"  [OK] {room.num} ({len(rasp_list)} пар)"))
                        success = True
                        break 
                        
                    except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError):
                        self.stdout.write(self.style.ERROR(f"  [!] Тайм-аут на {room.num}. Попытка {attempt+1}. Ждем 15с..."))
                        time.sleep(15)
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"  [ERR] {room.num}: {str(e)}"))
                        break

        self.stdout.write(self.style.SUCCESS('\nСинхронизация завершена успешно!'))