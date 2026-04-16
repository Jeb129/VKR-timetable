import requests
import time
import re
import logging
from datetime import datetime
from django.core.management.base import BaseCommand

from api.models import Institute, StudyProgram
from api.models.buildings import Classroom
from api.models.education_subjects import Discipline, LessonType, StudyGroup, Teacher
from api.models.schedule import Lesson, ScheduleScenario, Timeslot

logger = logging.getLogger(__name__)

def parse_group_info(group_code):
    """
    Разбирает строку типа '24-ИСбо-1'
    """
    # Паттерн: Год - Направление (Буквы) - Уровень - Форма - Номер
    pattern = r"(\d{2})-([А-Яа-я]+)([бмса])([озо])-([\w\d]+)"
    match = re.search(pattern, group_code)
    
    if not match:
        return None
        
    year_short, prog_abbr, stage_char, form_char, num = match.groups()
    
    # Маппинг для твоих моделей
    stages = {'б': 'Бакалавриат', 'м': 'Магистратура', 'с': 'Специалитет', 'а': 'Аспирантура'}
    forms = {'о': 'Очная', 'з': 'Заочная', 'в': 'Вечерняя'}
    
    return {
        'year': 2000 + int(year_short),
        'prog_code': prog_abbr.upper(), # Это пойдет в StudyProgram.code
        'stage': stages.get(stage_char, 'Бакалавриат'),
        'form': forms.get(form_char, 'Очная'),
        'group_num': num,
        'sub_group_num': int(re.search(r"п/г\s*(\d+)", group_code).group(1)) if "п/г" in group_code else None
    }

class Command(BaseCommand):
    help = 'Устойчивая синхронизация расписания EIOS через JSON API'
        
    def handle(self, *args, **options):
        # 1. Базовые объекты для связей
        inst, _ = Institute.objects.get_or_create(name="Импорт", short_name="ИМП")
        prog, _ = StudyProgram.objects.get_or_create(name="Общая", short_name="ОБЩ", institute=inst)
        
        scenario, _ = ScheduleScenario.objects.get_or_create(
            name="EIOS Import", 
            defaults={'is_active': True}
        )
        
        # Очищаем только уроки этого сценария перед началом, чтобы обновить данные
        Lesson.objects.filter(scenario=scenario).delete()

        rooms = Classroom.objects.exclude(eios_id__isnull=True)
        self.stdout.write(self.style.MIGRATE_LABEL(f"Найдено аудиторий: {rooms.count()}"))

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json'
        }
        import_dates = ["2026-03-30", "2026-04-06"]

        for room in rooms:
            for sdate in import_dates: # Добавляем вложенный цикл по датам
                url = f"https://eios.kosgos.ru/api/Rasp?idAudLine={room.eios_id}&sdate={sdate}"
                self.stdout.write(f"Запрос {room.num} на дату {sdate}...")
            
                success = False
                max_attempts = 5
                
                for attempt in range(max_attempts):
                    try:
                        time.sleep(1.5) # Базовая задержка между запросами
                        res = requests.get(url, headers=headers, timeout=20)
                        
                        if res.status_code == 429:
                            self.stdout.write(self.style.ERROR(f"  [!] Лимит запросов (429) на {room.num}. Ждем 10 сек... (Попытка {attempt+1}/{max_attempts})"))
                            time.sleep(10)
                            continue
                            
                        if res.status_code != 200:
                            self.stdout.write(self.style.WARNING(f"  [!] Ошибка {res.status_code}. Пробуем снова..."))
                            time.sleep(5)
                            continue

                        json_data = res.json()
                        rasp_list = json_data.get('data', {}).get('rasp', [])

                        if not rasp_list:
                            self.stdout.write(self.style.WARNING(f"  [?] Пустое расписание для {room.num}"))
                            success = True # Считаем успехом, просто пар нет
                            break

                        for item in rasp_list:
                            disc_full = item.get('дисциплина', 'Неизвестно')
                            teacher_fio = item.get('фиоПреподавателя')
                            group_name = item.get('группа')
                            day_idx = item.get('деньНедели')
                            order_num = item.get('номерЗанятия')
                            date_iso = item.get('дата')

                            # Парсинг названия
                            parts = disc_full.split(' ', 1)
                            type_name = parts[0].replace('.', '').strip()
                            discipline_name = parts[1].split(',')[0].strip() if len(parts) > 1 else disc_full

                            discipline, _ = Discipline.objects.get_or_create(name=discipline_name)
                            l_type, _ = LessonType.objects.get_or_create(name=type_name)

                            # Преподаватель и Группа
                            teacher = None
                            if teacher_fio:
                                teacher, _ = Teacher.objects.get_or_create(name=teacher_fio)
                            
                            group_name = item.get('группа')
                            group = None
                            if group_name and group_name != "Не указана":
                                info = parse_group_info(group_name)
                                
                                if info:
                                    # Ищем/Создаем направление подготовки
                                    # Поле 'code' теперь обязательно и уникально!
                                    current_prog, _ = StudyProgram.objects.get_or_create(
                                        code=info['prog_code'][:8], # Ограничение max_length=8
                                        defaults={
                                            'name': f"Направление {info['prog_code']}",
                                            'short_name': info['prog_code'], # Чтобы save не сгенерировал ерунду
                                            'institute': inst
                                        }
                                    )

                                    # Создаем группу
                                    group, _ = StudyGroup.objects.get_or_create(
                                        admission_year=info['year'],
                                        stud_program=current_prog,
                                        learning_form=info['form'],
                                        learning_stage=info['stage'],
                                        group_num=info['group_num'],
                                        sub_group_num=info['sub_group_num'],
                                        defaults={'students_count': 25}
                                    )

                            # Чётность недели
                            dt_obj = datetime.fromisoformat(date_iso.replace('Z', ''))
                            week_num = 1 if dt_obj.isocalendar()[1] % 2 != 0 else 2

                            slot = Timeslot.objects.filter(
                                day=day_idx,
                                order_number=order_num,
                                week_num=week_num
                            ).first()

                            if slot:
                                # Используем get_or_create для самого урока, чтобы избежать дублей
                                lesson, created = Lesson.objects.get_or_create(
                                    scenario=scenario,
                                    timeslot=slot,
                                    classroom=room,
                                    defaults={'discipline': discipline, 'lesson_type': l_type}
                                )
                                if teacher: lesson.teachers.add(teacher)
                                if group: lesson.study_groups.add(group)
                        
                        self.stdout.write(self.style.SUCCESS(f"  [OK] {room.num} синхронизирована ({len(rasp_list)} пар)"))
                        success = True
                        break # Выход из цикла попыток для этой комнаты

                    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                        self.stdout.write(self.style.ERROR(f"  [!] Ошибка соединения на {room.num}. Ждем 10 сек..."))
                        time.sleep(10)
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"  [ERR] Критический сбой на {room.num}: {str(e)}"))
                        break # Не повторяем при логических ошибках кода

                if not success:
                    self.stdout.write(self.style.ERROR(f"!!! Не удалось загрузить {room.num} после {max_attempts} попыток."))

            self.stdout.write(self.style.SUCCESS('\nСинхронизация полностью завершена!'))