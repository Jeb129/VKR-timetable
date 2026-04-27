import requests
import time
import re
import logging
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from api.models.schedule import Semester

# Импорты обновлены согласно вашей новой структуре
from api.models.education_subjects import Institute, StudyProgram, Discipline, LessonType, StudyGroup, Teacher
from api.models.buildings import Classroom
from api.models.schedule import Lesson, ScheduleScenario, Timeslot

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

class Command(BaseCommand):
    help = 'Устойчивая синхронизация расписания EIOS через JSON API'
        
    def handle(self, *args, **options):
        inst, _ = Institute.objects.get_or_create(name="Импорт", short_name="ИМП")
        scenario, _ = ScheduleScenario.objects.get_or_create(
            name="EIOS Import", 
            defaults={'is_active': True}
        )

        import_dates = ["2026-03-30", "2026-04-06"]
        
        # Берем первую дату из списка импорта
        first_import_date = datetime.strptime(import_dates[0], "%Y-%m-%d").date()
        
        # Пытаемся найти существующий семестр, в который попадает эта дата
        semester = Semester.objects.filter(
            date_start__lte=first_import_date,
            date_end__gte=first_import_date
        ).first()

        # Если сеmeстр не найден — создаем его автоматически
        if not semester:
            self.stdout.write(self.style.WARNING("Подходящий семестр не найден. Создаю новый..."))
            semester = Semester.objects.create(
                name=f"Семестр импорта ({first_import_date.strftime('%Y')})",
                date_start=first_import_date - timedelta(days=30), # Запас назад
                date_end=first_import_date + timedelta(days=120)   # Запас вперед (4 месяца)
            )
        
        # Привязываем сценарий к этому семестру
        scenario, _ = ScheduleScenario.objects.get_or_create(
            name="EIOS Import", 
            defaults={'is_active': True, 'semester': semester}
        )
        
        # Если сценарий уже был, но семестр изменился — обновляем
        if scenario.semester != semester:
            scenario.semester = semester
            scenario.save()

        self.stdout.write(self.style.SUCCESS(f"Работаем в семестре: {semester.name}"))
        self.stdout.write(self.style.WARNING("Очистка старых данных сценария..."))
        Lesson.objects.filter(scenario=scenario).delete()

        rooms = Classroom.objects.exclude(eios_id__isnull=True)
        total_rooms = rooms.count()
        self.stdout.write(self.style.MIGRATE_LABEL(f"Найдено аудиторий в БД: {total_rooms}"))

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json'
        }
        import_dates = ["2026-03-30", "2026-04-06"]

        room_counter = 0
        for room in rooms:
            room_counter += 1
            if room_counter % 40 == 0:
                self.stdout.write(self.style.MIGRATE_LABEL(f"Прогресс: {room_counter}/{total_rooms}. Пауза 45 сек..."))
                time.sleep(45)

            for sdate in import_dates:
                url = f"https://eios.kosgos.ru/api/Rasp?idAudLine={room.eios_id}&sdate={sdate}"
                self.stdout.write(f"Запрос {room.num} на {sdate}...")
            
                success = False
                for attempt in range(5):
                    try:
                        time.sleep(1.5) 
                        res = requests.get(url, headers=headers, timeout=20)
                        
                        if res.status_code == 429:
                            time.sleep(15)
                            continue
                            
                        if res.status_code != 200:
                            time.sleep(5)
                            continue

                        json_data = res.json()
                        rasp_list = json_data.get('data', {}).get('rasp', [])

                        for item in rasp_list:
                            disc_full = item.get('дисциплина', 'Неизвестно')
                            teacher_fio = item.get('фиоПреподавателя')
                            day_idx = item.get('деньНедели')
                            order_num = item.get('номерЗанятия')
                            date_iso = item.get('дата')

                            parts = disc_full.split(' ', 1)
                            type_name = parts[0].replace('.', '').strip()
                            discipline_name = parts[1].split(',')[0].strip() if len(parts) > 1 else disc_full

                            discipline, _ = Discipline.objects.get_or_create(name=discipline_name)
                            l_type, _ = LessonType.objects.get_or_create(name=type_name)

                            teacher = None
                            if teacher_fio:
                                teacher, _ = Teacher.objects.get_or_create(
                                    name=teacher_fio, defaults={'constraint_weight': 1}
                                )
                            
                            group_name = item.get('group') or item.get('группа')
                            group = None
                            if group_name and group_name != "Не указана":
                                info = parse_group_info(group_name)
                                if info:
                                    current_prog, _ = StudyProgram.objects.get_or_create(
                                        code=info['prog_code'][:8],
                                        defaults={'name': f"Направление {info['prog_code']}", 'short_name': info['prog_code'], 'institute': inst}
                                    )
                                    # ИСПРАВЛЕНО: study_program вместо stud_program
                                    group, _ = StudyGroup.objects.get_or_create(
                                        admission_year=info['year'],
                                        study_program=current_prog,
                                        learning_form=info['form'],
                                        learning_stage=info['stage'],
                                        group_num=info['group_num'],
                                        sub_group_num=info['sub_group_num'],
                                        defaults={'students_count': 25}
                                    )

                            dt_obj = datetime.fromisoformat(date_iso.replace('Z', ''))
                            week_num = 1 if dt_obj.isocalendar()[1] % 2 != 0 else 2

                            slot = Timeslot.objects.filter(day=day_idx, order_number=order_num, week_num=week_num).first()

                            if slot:
                                lesson, created = Lesson.objects.get_or_create(
                                    scenario=scenario, timeslot=slot, classroom=room,
                                    defaults={'discipline': discipline, 'lesson_type': l_type}
                                )
                                if teacher: lesson.teachers.add(teacher)
                                if group: lesson.study_groups.add(group)
                        
                        self.stdout.write(self.style.SUCCESS(f"  [OK] {room.num} ({len(rasp_list)} пар)"))
                        success = True
                        break
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"  [ERR] {room.num}: {str(e)}"))
                        time.sleep(2)
                if not success: self.stdout.write(self.style.ERROR(f"!!! Ошибка {room.num}"))

        self.stdout.write(self.style.SUCCESS('\nСинхронизация завершена!'))