from dataclasses import dataclass
from datetime import datetime
import logging
import re
from typing import Any, Dict, List

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from api.models import *
from api.services.data_import.excel import export_excel
from api.services.data_import.structure import (ACADEMIC_LOAD_STRUCTURE)
from api.services.data_import.validator import ValidationMessage, validate_row
from api.services.schedule.mapper import get_semester_by_date

logger = logging.getLogger("data_import")

class AcademicLoadReader:
    def __init__(self,data):
        self.data = data
        self.errors = []

        # Счетчики - Обработка строк
        self.skipped_counter = 0 # Пропущенные строки
        self.error_counter = 0 # Строки с необработанными ошибками
        self.success_counter = 0 # Успешно обработанные строки

        # Счетчики - загружаемые объекты
        self.programs_created_counter = 0 # Созданные направления подготовки
        self.programs_exists_counter = 0 # Уже существующие направления подготовки

        self.discipline_created_counter = 0 # Созданные дисциплины
        self.discipline_exists_counter = 0 # Уже существующие дисциплины

        self.teachers_created_counter = 0 # Созданные преподаватели
        self.teachers_exists_counter = 0 # Существующие преподаватели

        self.groups_created_counter = 0 # Созданные группы
        self.groups_exists_counter = 0 # Существующие группы

        self.load_created_counter = 0 # Созданные записи нагрузки
        self.load_exists_counter = 0 # Существующие записис нагрузки
        
        # Временные хранилища (чтобы не дергать БД каждый раз)
        self.programs = {}     # code -> {code, name, institute}
        self.teachers = {}     # fio -> {name, post}
        self.disciplines = {}
        self.groups = {}

        self.groups_raw = {} # Группы без подгруппы, для постобработки
        self.load_raw = [] # Академическая нагрузка для групп без подгрупп

    def __iter__(self):
        
        def skip(idx,field,message):
            msg = ValidationMessage(
                idx,"ERROR",field,message
            )
            self.errors.append(msg)
            self.skipped_counter += 1
            return msg
        
        def error(idx,field,message):
            msg = ValidationMessage(
                idx,"CRITICAL",field,message
            )
            self.errors.append(msg)
            self.error_counter += 1
            return msg

        for idx, row in enumerate(self.data):
            row_errors, (
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

            merge_key) = validate_row(row,idx)

            if row_errors:
                self.errors.extend(row_errors)
                self.skipped_counter += 1
                for msg in row_errors:
                    yield msg
                continue

            # Обработка строки
            with transaction.atomic():
                try:
                    # Направление подготовки
                    if study_program_code not in self.programs:
                        institute_obj = Institute.objects.filter(
                        short_name=institute_short_name
                        ).first()
                        if not institute_obj:
                            yield skip(idx,"Направление.Институт",
                                       f"Не найден институт {institute_short_name}")
                            continue

                        study_program_obj, created = StudyProgram.objects.get_or_create(
                                institute=institute_obj,
                                code=study_program_code,
                                defaults={
                                    "name": study_program_name, 
                                    "short_name": study_program_short_name
                                    },
                            )
                        
                        self.programs[study_program_code] = study_program_obj
                        if created:
                            self.programs_created_counter += 1
                        else:
                            self.programs_exists_counter += 1
                    else:
                        study_program_obj = self.programs[study_program_code]

                    # Дисциплина
                    if discipline_name not in self.disciplines:
                        discipline_obj, created = Discipline.objects.get_or_create(
                            name=discipline_name,
                            defaults={
                                "allow_merge_teachers": not not d_allow_merge_teachers
                                }
                            )
                        self.disciplines[discipline_name] = discipline_obj
                        if created:
                            self.discipline_created_counter += 1
                        else:
                            self.discipline_exists_counter += 1
                    else:
                        discipline_obj = self.disciplines[discipline_name]
                    
                    # Вид занятия
                    lesson_type_obj = LessonType.objects.filter(
                        Q(name = lesson_type_name) | Q(short_name = lesson_type_short_name)
                    ).first()
                    if not lesson_type_obj:
                        yield skip(idx,"Вид занятия",
                            f"Не найден вид занятия {lesson_type_name}, {lesson_type_short_name}")
                        continue
                    
                    # Преподаватель
                    if (teacher_institute_short_name,teacher_name) not in self.teachers:
                        if teacher_institute_short_name:
                            teacher_inst_obj = Institute.objects.filter(
                            short_name=teacher_institute_short_name
                            ).first()
                        else:
                            teacher_inst_obj = None
                        if teacher_inst_obj:
                            teacher_obj, created = Teacher.objects.get_or_create(
                                institute=teacher_inst_obj,
                                name = teacher_name,
                                defaults={
                                    "post":teacher_post
                                }
                            )
                        else:
                            teacher_obj, created = Teacher.objects.get_or_create(
                                name = teacher_name,
                                defaults={
                                    "post":teacher_post
                                }
                            )
                        self.teachers[(teacher_institute_short_name,teacher_name)] = teacher_obj
                        if created:
                            self.teachers_created_counter += 1
                        else:
                            self.teachers_exists_counter += 1
                    else:
                        teacher_obj =  self.teachers[(teacher_institute_short_name,teacher_name)]
                    
                    # Семестр
                    start_year = admission_year + (semester_order) // 2
                    month = 2 if semester_order % 2 == 0 else 9

                    dt = f"{start_year}-{month:02d}-01"
                    semester_obj = get_semester_by_date(dt)
                    if not semester_obj:
                            yield skip(idx,"Нагрузка.Номер семестра",
                                f"Не найден семестр {semester_order} для групп, поступивших в {admission_year} (Расчитанная дата: {dt})")
                            continue
                    
                    # Нагрузка
                    group_key = (study_program_code, 
                                    admission_year,
                                    group_num,
                                    learning_form,
                                    learning_stage,
                                    sub_group_num)
                    if sub_group_num is None:
                        if group_key not in self.groups_raw:
                            g_obj = StudyGroup(
                                    study_program=study_program_obj,
                                    admission_year=admission_year,
                                    group_num=group_num,
                                    learning_form=learning_form,
                                    learning_stage=learning_stage,
                                    students_count=students_count)
                                
                            self.groups_raw[group_key] = g_obj
                        else:
                            g_obj = self.groups_raw[group_key]
                        
                        self.load_raw.append(
                                    AcademicLoad(
                                        semester=semester_obj,
                                        discipline=discipline_obj,
                                        lesson_type=lesson_type_obj,
                                        teacher=teacher_obj,
                                        study_group=g_obj,
                                        control_type=control_type,
                                        whole_hours=hours,
                                        whole_weeks=weeks,     
                                    )
                                )
                    else:
                        if group_key not in self.groups:
                            g_obj, created = StudyGroup.objects.get_or_create(
                                    study_program=study_program_obj,
                                    admission_year=admission_year,
                                    group_num=group_num,
                                    learning_form=learning_form,
                                    learning_stage=learning_stage,
                                    students_count=students_count,
                                    sub_group_num=int(sub_group_num)
                                )
                            self.groups[group_key] = g_obj
                            if created:
                                self.groups_created_counter += 1
                            else:
                                self.groups_exists_counter += 1
                        else:
                            g_obj = self.groups[group_key]
                        _, created = AcademicLoad.objects.get_or_create(
                                semester=semester_obj,
                                discipline=discipline_obj,
                                lesson_type=lesson_type_obj,
                                teacher=teacher_obj,
                                study_group=g_obj,
                                control_type=control_type,
                                whole_hours=hours,
                                whole_weeks=weeks,
                                defaults={
                                    "merge_key":merge_key
                                }
                        )
                        if created:
                            self.load_created_counter += 1
                        else:
                            self.load_exists_counter += 1
                    self.success_counter += 1
                except Exception as err:
                    yield error(idx,err.__class__.__name__,err)

        for _,raw_group in self.groups_raw.items():
                try:
                    with transaction.atomic():
                        subs = list(StudyGroup.objects.filter(
                                    admission_year = raw_group.admission_year,
                                    study_program = raw_group.study_program,
                                    learning_form = raw_group.learning_form,
                                    learning_stage = raw_group.learning_stage,
                                    group_num = raw_group.group_num,
                                    sub_group_num__isnull=False
                                ).all())
                        count = len(subs)
                        if count == 0:
                            # Если нет аналогичных групп с номерами подгрупп - создаем группу
                            group, created = StudyGroup.objects.get_or_create(
                                admission_year = raw_group.admission_year,
                                study_program = raw_group.study_program,
                                learning_form = raw_group.learning_form,
                                learning_stage = raw_group.learning_stage,
                                students_count = raw_group.students_count,
                                group_num = raw_group.group_num,
                                # sub_group_num = None
                            )
                            if created:
                                self.groups_created_counter += 1
                            else:
                                self.groups_exists_counter += 1
                            subs.append(group)
                            count += 1

                        academic_loads = [a for a in self.load_raw if (
                            a.study_group.admission_year == raw_group.admission_year and
                            a.study_group.study_program == raw_group.study_program and
                            a.study_group.learning_form == raw_group.learning_form and
                            a.study_group.learning_stage == raw_group.learning_stage and
                            a.study_group.group_num == raw_group.group_num
                            )]


                        
                        for i in range(count):
                            # Создаем нагрузку для каждой подгруппы
                            for raw_load in academic_loads:
                                _, created = AcademicLoad.objects.get_or_create(
                                    semester=raw_load.semester,
                                    discipline=raw_load.discipline,
                                    lesson_type=raw_load.lesson_type,
                                    teacher=raw_load.teacher,
                                    study_group=subs[i],
                                    whole_hours =raw_load.whole_hours,
                                    whole_weeks =raw_load.whole_weeks,
                                    defaults={
                                        "merge_key":raw_load.merge_key
                                        }
                                    )
                                if created:
                                    self.load_created_counter += 1
                                else:
                                    self.load_exists_counter += 1                          
                            # Соединяем группы в подгруппы
                            for j in range(i+1,count):
                                subs[i].sub_groups.add(subs[j])
                    # self.success_counter += 1
                except Exception as err:
                    yield error(idx,err.__class__.__name__,err)


def export_loading(target,queryset = None):
    if queryset is None:
        queryset = AcademicLoad.objects
    qs = queryset.select_related(
        "discipline",
        "lesson_type",
        "teacher",
        "study_group",
        "study_group__study_program",
        "study_group__study_program__institute",
        "semester",
    ).all()

    data = []

    for load in qs:
        group = load.study_group
        stud_program = group.study_program
        institute = stud_program.institute
        teacher_institute = load.teacher.institute.short_name if load.teacher.institute else None

        # --- вычисление номера семестра ---
        # 26.04.2026 - Перенесено в property модели AcademicLoad
        

        row = [
            # load.id,
            # Направление
            institute.short_name,
            stud_program.code,
            stud_program.name,
            stud_program.short_name,

            # Дисциплина
            load.discipline.name,
            load.discipline.allow_merge_teachers,

            # Вид занятия
            load.lesson_type.name,
            load.lesson_type.short_name,

            # Нагрузка
            load.semester_order,
            load.control_type,
            load.whole_weeks,
            load.whole_hours,

            # Преподаватель
            teacher_institute,
            load.teacher.name,
            load.teacher.post,

            # Группа
            group.admission_year,
            group.group_num,
            group.sub_group_num,
            group.learning_form,
            group.learning_stage,
            group.students_count,

            load.merge_key,
        ]

        data.append(row)

    export_excel(target, data, ACADEMIC_LOAD_STRUCTURE)