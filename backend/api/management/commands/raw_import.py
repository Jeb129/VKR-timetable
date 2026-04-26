from ast import Try
import math
import re
import sys

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.forms.models import model_to_dict


from api.models import *
from api.services.data_import.excel import import_excel
from api.services.data_import.loaders import AcademicLoadReader
from api.services.data_import.structure import ACADEMIC_LOAD_STRUCTURE
from api.services.schedule.mapper import get_semester_by_date


def safe_str(x):
    if x is None:
        return None
    if isinstance(x, float) and math.isnan(x):
        return None
    return str(x).strip()


def clean_direction_code(code):
    s = safe_str(code)
    if not s:
        return None
    return s[:-1] if s.endswith('.') else s


def normalize_teacher_name(name):
    s = safe_str(name)
    if not s:
        return None
    return re.sub(r"\s+", " ", s)

def parse_semester(admission_year: int, sem_raw: str):
    """
    sem_raw: '3/2', '4/7' – последний номер это семестр
    """
    s = safe_str(sem_raw)
    if not s or "/" not in s:
        return None

    try:
        _, sem_num = s.split("/")
        sem_num = int(sem_num)
    except:
        return None

    start_year = admission_year + (sem_num) // 2
    month = 3 if sem_num % 2 == 0 else 10

    dt = f"{start_year}-{month:02d}-01"
    return get_semester_by_date(dt)


def create_welldone_data(data):
    result = []
    for idx, row in enumerate(data):
        try:
            institute_short_name = safe_str(row[9])
            study_program_code = clean_direction_code(row[4])
            study_program_name = safe_str(row[5])
            study_program_short_name = safe_str(row[5])

            discipline_name = safe_str(row[12])
            if discipline_name is None:
                discipline_name = safe_str(row[11])
            d_allow_merge_teachers = None

            lesson_type_name = None
            lesson_type_short_name = safe_str(row[18])

            semester_order= int(safe_str(row[14]).split('/')[1])
            control_type = safe_str(row[20])
            weeks = row[17]
            hours = row[19]

            teacher_institute_short_name = None
            teacher_name = normalize_teacher_name(row[35])
            teacher_post = safe_str(row[36])

            admission_year = 2000 + int(safe_str(row[15]).split(sep="-")[0])
            group_num = safe_str(row[15]).split(sep="-")[2]
            sub_group_num = safe_str(row[11]).split("п/г ")[1][0] if "п/г" in str(row[11]) else None
            learning_form = safe_str(row[54])
            learning_stage = safe_str(row[53])
            students_count = row[16]

            merge_key = None

            result.append([
                institute_short_name,
                study_program_code,
                study_program_name,
                study_program_short_name,
                discipline_name,
                d_allow_merge_teachers,
                lesson_type_name,
                lesson_type_short_name,
                semester_order,
                control_type,
                weeks,
                hours,
                teacher_institute_short_name,
                teacher_name,
                teacher_post,
                admission_year,
                group_num,
                sub_group_num,
                learning_form,
                learning_stage,
                students_count,
                merge_key
            ])
        except:
            continue
    
    return result

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("im_ebanko", type=bool, help="Мне безразличны последствия загрузки кривого файла в базу\nЯ подтверждаю что сделал копию / готов депнуть БД / использую эту функцию в первый и последний раз\n\nЛучше воспользуйся excel_import")

    def handle(self, *args, **kwargs):
        
        bypass = kwargs["im_ebanko"]
        if not bypass:
            self.stdout.write(self.style.ERROR("Подтверди свою готовность к последствиям\nПодробности в help"))
            return
        
        self.stdout.write(self.style.NOTICE(f"Ну чтож, бог тебе в помощь..."))

        excel_path = settings.DATA_FILES_DIR / "raw_import.xlsx"
        if not excel_path.exists():
            self.stdout.write(self.style.ERROR("Файл не найден"))
            return
        self.stdout.write(f"Чтение файла....")
        data = import_excel(excel_path)
        data = create_welldone_data(data)
        self.stdout.write(f"Прочитано строк: {len(data)}")
        self.stdout.write(f"Загрузка данных....")

        load_stream = AcademicLoadReader(data)

        for msg in load_stream:
            match msg.level:
                case "WARNING":
                    self.stdout.write(self.style.WARNING(msg))
                case "ERROR":
                    self.stdout.write(self.style.HTTP_NOT_FOUND(msg))
                case "CRITICAL":
                    self.stdout.write(self.style.NOTICE(msg))


        self.stdout.write()
        self.stdout.write(self.style.SUCCESS(f"Успешно обработано строк {load_stream.success_counter}"))
        self.stdout.write(self.style.WARNING(f"Пропущено строк {load_stream.skipped_counter}"))
        self.stdout.write(self.style.ERROR(f"Строк с ошибками {load_stream.error_counter}"))
                        
        self.stdout.write()
        self.stdout.write(self.style.HTTP_INFO(f"Создано направлений подгатовки: {load_stream.programs_created_counter}"))
        self.stdout.write(self.style.HTTP_INFO(f"Сщздано учебных групп: {load_stream.groups_created_counter}"))
        self.stdout.write(self.style.HTTP_INFO(f"Создано преподавателей: {load_stream.teachers_created_counter}"))
        self.stdout.write(self.style.HTTP_INFO(f"Создано записей нагрузки: {load_stream.load_created_counter}"))
        
        self.stdout.write()
        self.stdout.write(self.style.HTTP_INFO(f"Найдено существующих направлений подгатовки: {load_stream.programs_exists_counter}"))
        self.stdout.write(self.style.HTTP_INFO(f"Найдено существующих учебных групп: {load_stream.groups_exists_counter}"))
        self.stdout.write(self.style.HTTP_INFO(f"Найдено существующих преподавателей: {load_stream.teachers_exists_counter}"))
        self.stdout.write(self.style.HTTP_INFO(f"Найдено существующих записей нагрузки: {load_stream.load_exists_counter}"))