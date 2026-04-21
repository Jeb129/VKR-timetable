from ast import Try
import math
import re
import sys

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction


from api.models import *
from api.services.data_import.excel import import_excel
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


def extract_group_parts(raw):
    """
    Пример:
    '22-ИСбо-1 п/г 2' → ('22-ИСбо-1', '2')
    '22-ИСбо-1' → ('22-ИСбо-1', None)
    """
    s = safe_str(raw)
    if not s:
        return None, None

    # subgroup?
    sub_match = re.search(r"п/г\s*(\d+)", s)
    subgroup = sub_match.group(1) if sub_match else None

    base = s.split("п/г")[0].strip()

    return base, subgroup


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

    start_year = admission_year + (sem_num - 1) // 2
    month = 3 if sem_num % 2 == 0 else 10

    dt = f"{start_year}-{month:02d}-01"
    return get_semester_by_date(dt)


class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        excel_path = settings.BASE_DIR / "../../Nagruzka.xlsx"
        if not excel_path.exists():
            self.stdout.write(self.style.ERROR("Файл не найден"))
            return

        data = import_excel(excel_path)
        self.stdout.write(f"Прочитано строк: {len(data)}")
        success_counter = 0
        # КЭШИ ДЛЯ ОДНОГО ПРОХОДА
        programs = {}     # code -> {code, name, institute}
        teachers = {}     # fio -> {name, post}


        groups = {}       # (code, year, base_group) -> {...}
        academic_load_raw = [] # список dict для дальнейшей загрузки

        for idx, row in enumerate(data, start=3):
            # sys.stdout.write(f"\rОбработка строки {idx}...")
            # sys.stdout.flush()
            # фильтры из твоего кода
            if row[18] not in ["Лаб", "Лек", "Пр"]:
                continue
            if row[8] < 2021:
                continue

            # ---- ПОЛЯ ----
            institute_raw = safe_str(row[9])
            study_program_code = clean_direction_code(row[4])
            study_program_name = safe_str(row[5])

            discipline_name = safe_str(row[12])
            if discipline_name is None:
                discipline_name = safe_str(row[11])

            lesson_type_name = safe_str(row[18])
            control_type = safe_str(row[20])
            hours = row[19]
            weeks = row[17]

            teacher_name = normalize_teacher_name(row[35])
            if not teacher_name:
                self.stdout.write(
                    self.style.WARNING(f"Строка {idx}: не заполнено имя преподавателя")
                )
                continue


            teacher_post = safe_str(row[36])  # но не участвует в ключе

            admission_year = row[8]
            group_num = safe_str(row[15]).split(sep="-")[2]
            sub_group_num = safe_str(row[11]).split("п/г ")[1][0] if "п/г" in str(row[11]) else None
            learning_form = safe_str(row[54])
            learning_stage = safe_str(row[53])
            students_count = row[16]

            sem_raw = safe_str(row[14])
            sem = parse_semester(admission_year, sem_raw)

            # print('id:', idx, "data:", 
            #       institute_raw,
            #       study_program_code,
            #       study_program_name,
            #       discipline_name,
            #       lesson_type_name,
            #       control_type,
            #       hours,
            #       weeks,
            #       teacher_name,
            #       teacher_post,
            #       admission_year,
            #       group_num,
            #       sub_group_num,
            #       learning_form,
            #       learning_stage,
            #       students_count)

            if not sem:
                continue  # не создаём нагрузку, если семестр не вычислен
            
            with transaction.atomic():
                try:
                    # ---- ДИСЦИПЛИНА + ВИД ----
                    discipline, _ = Discipline.objects.get_or_create(name=discipline_name)
                    lt, _ = LessonType.objects.get_or_create(name=lesson_type_name)

                    # ---- НАПРАВЛЕНИЕ ----
                    if study_program_code not in programs:
                        inst_obj = Institute.objects.filter(short_name=institute_raw).first()

                        if not inst_obj:
                            self.stdout.write(
                                self.style.WARNING(f"Строка {idx}: не найден институт {institute_raw}")
                            )
                            continue
                            
                        prog, _ = StudyProgram.objects.get_or_create(
                            institute=inst_obj,
                            code=study_program_code,
                            defaults={"name": study_program_name},

                        )
                        programs[study_program_code] = prog
                    else:
                        prog = programs[study_program_code]

                
                    # ---- ПРЕПОДАВАТЕЛЬ ----
                    # ключ = Фамилия И.О.
                    if teacher_name not in teachers:
                        t_obj, _ = Teacher.objects.get_or_create(
                            name=teacher_name,
                            defaults={"post": teacher_post},
                        )
                        teachers[teacher_name] = t_obj
                    else:
                        t_obj = teachers[teacher_name]
                    
                    # ---- ГРУППА ----
                    # ключ = базовая группа + код направления + год приёма

                    
                    if sub_group_num is None:
                            # Если нет номера подгруппы - сохраняем для постобработки
                            group_key = (study_program_code, 
                                 admission_year,
                                 group_num,
                                 learning_form,
                                 learning_stage,
                                 sub_group_num)
                            
                            g_obj = StudyGroup(
                                stud_program=prog,
                                admission_year=admission_year,
                                group_num=group_num,
                                learning_form=learning_form,
                                learning_stage=learning_stage,
                                students_count=students_count)
                            
                            groups[group_key] = g_obj

                            academic_load_raw.append(
                                AcademicLoad(
                                    semester=sem,
                                    discipline=discipline,
                                    lesson_type=lt,
                                    teacher=t_obj,
                                    study_group=g_obj,
                                    whole_hours=hours,
                                    whole_weeks=weeks,     
                                )
                            )
                    else:
                        g_obj, _ = StudyGroup.objects.get_or_create(
                            stud_program=prog,
                            admission_year=admission_year,
                            group_num=group_num,
                            learning_form=learning_form,
                            learning_stage=learning_stage,
                            students_count=students_count,
                            sub_group_num=int(sub_group_num)
                        )
                        # ---- СОЗДАЁМ НАКРУЗКУ ----
                        AcademicLoad.objects.get_or_create(
                                semester=sem,
                                discipline=discipline,
                                lesson_type=lt,
                                teacher=t_obj,
                                study_group=g_obj,
                                whole_hours=hours,
                                whole_weeks=weeks,
                        )
                    success_counter+=1
                except Exception as err:
                    self.stdout.write(self.style.ERROR(f"Ошибка строки {idx}: {err}"))

        self.stdout.write(self.style.SUCCESS(f"Успешно обработано строк {success_counter}"))
                

        # Постобработка групп без номера подгруппы и их академической нагрузки

        for idx, (key,raw_group) in enumerate(groups.items()):
            try:
                with transaction.atomic():
                    subs = list(StudyGroup.objects.filter(
                                admission_year = raw_group.admission_year,
                                stud_program = raw_group.stud_program,
                                learning_form = raw_group.learning_form,
                                learning_stage = raw_group.learning_stage,
                                group_num=raw_group.group_num,
                                sub_group_num__isnull=False
                            ).all())
                    count = len(subs)
                    if count == 0:
                        # Если нет аналогичных групп с номерами подгрупп - создаем группу
                        group, _ = StudyGroup.objects.get_or_create(
                            admission_year = raw_group.admission_year,
                            stud_program = raw_group.stud_program,
                            learning_form = raw_group.learning_form,
                            learning_stage = raw_group.learning_stage,
                            students_count = raw_group.students_count,
                            group_num=raw_group.group_num,
                        )
                        subs.append(group)

                        
                    academic_loads = [a for a in academic_load_raw if a.study_group == raw_group]
                    for i in range(count):
                        # Создаем нагрузку для каждой подгруппы
                        for raw_load in academic_loads:
                            AcademicLoad.objects.get_or_create(
                            semester=raw_load.semester,
                            discipline=raw_load.discipline,
                            lesson_type=raw_load.lesson_type,
                            teacher=raw_load.teacher,
                            study_group=subs[i],
                            whole_hours =raw_load.whole_hours ,
                            whole_weeks =raw_load.whole_weeks,
                        )
                        # Соединяем группы в подгруппы
                        for j in range(i+1,count):
                            subs[i].sub_groups.add(subs[j])
            except Exception as err:
                    self.stdout.write(self.style.ERROR(f"Ошибка постобработки группы {key} {raw_group}: {err}"))