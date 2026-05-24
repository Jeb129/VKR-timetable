import logging

from django.db import transaction
from django.db.models import Q

from api.models import *
from api.services.data_import.excel import export_excel
from api.services.data_import.structure import (ACADEMIC_LOAD_STRUCTURE)
from api.services.data_import.validator import ValidationMessage, validate_load_row
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

        self.disciplines_created_counter = 0 # Созданные дисциплины
        self.disciplines_exists_counter = 0 # Уже существующие дисциплины

        self.teachers_created_counter = 0 # Созданные преподаватели
        self.teachers_exists_counter = 0 # Существующие преподаватели

        self.groups_created_counter = 0 # Созданные группы
        self.groups_exists_counter = 0 # Существующие группы !!!Работает криво!!!

        self.load_created_counter = 0 # Созданные записи нагрузки
        self.load_exists_counter = 0 # Существующие записис нагрузки !!!Работает криво!!!
        
        # Кэш для создаваемых объектов
        self.programs = {}     # code -> {code, name, institute}
        self.teachers = {}     # fio -> {name, post}
        self.disciplines = {}
        self.groups = {}

        # Кэши справочников
        self.semesters = {}
        self.institutes_cache = {i.short_name: i for i in Institute.objects.all()}
        self.lesson_types_cache = {lt.name: lt for lt in LessonType.objects.all()}
        self.lesson_types_cache.update({lt.short_name: lt for lt in LessonType.objects.all() if lt.short_name})

        # Постобработка
        self.queue_groups = [] # Группы без подгруппы, для постобработки
        self.queue_flow = [] # Группы без номера группы и подгруппы (потоки), для постобработки
        self.linked_groups = set() # Хранилище для отслеживания уже связанных групп (чтобы не дергать БД лишний раз)

    def _skip(self,idx,field,message):
        msg = ValidationMessage(
            idx,"ERROR",field,message
        )
        self.errors.append(msg)
        self.skipped_counter += 1
        return msg
    
    def _error(self,idx,field,message):
        msg = ValidationMessage(
            idx,"CRITICAL",field,message
        )
        self.errors.append(msg)
        self.error_counter += 1
        return msg

    def _get_semester(self, adm_year, sem_order):
        sem_year = adm_year + (sem_order // 2)
        sem_month = 2 if sem_order % 2 == 0 else 9
        dt_key = f"{sem_year}-{sem_month:02d}-01"
        
        if dt_key not in self.semesters:
            self.semesters[dt_key] = get_semester_by_date(dt_key)
        return self.semesters[dt_key]

    def process_row(self, idx, norm, mode):
        """
        Единый метод обработки одной нормализованной строки.
        mode: subgroup | group | stream
        """
        (inst_short, sp_code, sp_name, sp_short, d_name, d_merge, 
         lt_name, lt_short, sem_order, control, weeks, hours, 
         t_inst_short, t_name, t_post, adm_year, g_num, sub_g_num, 
         l_form, l_stage, stud_count, m_key) = norm

        with transaction.atomic():
            try:
                # 1. Получаем общие объекты (используя кэш)
                inst_obj = self.institutes_cache.get(inst_short)
                if not inst_obj:
                    yield self._skip(idx, "Институт", f"Не найден: {inst_short}")
                    return
                
                # Вид занятия
                lt_obj = self.lesson_types_cache.get(lt_name) or self.lesson_types_cache.get(lt_short)
                if not lt_obj:
                    yield self._skip(idx, "Вид занятия", f"Не найден: {lt_name}, {lt_short}")
                    return

                # Семестр
                sem_obj = self._get_semester(adm_year, sem_order)
                if not sem_obj:
                    yield self._skip(idx, "Семестр", f"Не найден для {adm_year} год, {sem_order} сем.")
                    return
                
                # Программа
                if sp_code not in self.programs:
                    sp_obj, created = StudyProgram.objects.get_or_create(
                        code=sp_code, institute=inst_obj, 
                        defaults={"name": sp_name, "short_name": sp_short}
                    )
                    self.programs[sp_code] = sp_obj
                    if created:
                        self.programs_created_counter += 1
                    else:
                        self.programs_exists_counter += 1
                sp_obj = self.programs[sp_code]

                # Дисциплина
                if d_name not in self.disciplines:
                    d_obj, created = Discipline.objects.get_or_create(
                        name=d_name, defaults={"allow_merge_teachers": bool(d_merge)}
                    )
                    self.disciplines[d_name] = d_obj
                    if created:
                        self.disciplines_created_counter += 1
                    else:
                        self.disciplines_exists_counter += 1
                d_obj = self.disciplines[d_name]



                # Преподаватель (get_or_create с кэшем)
                t_key = (t_inst_short, t_name)
                if t_key not in self.teachers:
                    # Поиск института преподавателя (опционально)
                    t_inst = self.institutes_cache.get(t_inst_short)
                    t_obj, created = Teacher.objects.get_or_create(
                        name=t_name, institute=t_inst, defaults={"post": t_post}
                    )
                    self.teachers[t_key] = t_obj
                    if created:
                        self.teachers_created_counter += 1
                    else:
                        self.teachers_exists_counter += 1
                t_obj = self.teachers[t_key]



                # 2. ПОИСК / СОЗДАНИЕ ГРУПП (Логика зависит от mode)
                target_groups = []
                
                # Общий фильтр потока
                base_filter = {
                    "study_program": sp_obj,
                    "admission_year": adm_year,
                    "learning_form": l_form,
                    "learning_stage": l_stage,
                }

                if mode == "subgroup":
                    # Создаем/находим конкретную подгруппу
                    g_obj, created = StudyGroup.objects.get_or_create(
                        group_num=g_num, sub_group_num=sub_g_num,
                        **base_filter,
                        defaults={"students_count": stud_count}
                    )
                    target_groups = [g_obj]
                    if created:
                        self.groups_created_counter += 1
                    else:
                        self.groups_exists_counter += 1

                elif mode == "group":
                    # Ищем все подгруппы этой группы
                    target_groups = list(StudyGroup.objects.filter(group_num=g_num, **base_filter))
                    if not target_groups:
                        # Если подгрупп не было создано в 1-м цикле, создаем саму группу (sub_group=None)
                        g_obj, created = StudyGroup.objects.get_or_create(
                            group_num=g_num, sub_group_num=None,
                            **base_filter,
                            defaults={"students_count": stud_count}
                        )
                        target_groups = [g_obj]
                        if created:
                            self.groups_created_counter += 1
                        else:
                            self.groups_exists_counter += 1
                    else:
                        # --- ВОТ ЭТОТ МОМЕНТ: Связываем подгруппы между собой ---
                        group_key = (sp_code, adm_year, g_num, l_form, l_stage)
                        if group_key not in self.linked_groups:
                            count = len(target_groups)
                            for i in range(count):
                                for j in range(i + 1, count):
                                    # Благодаря symmetrical=True в модели, связь создастся в обе стороны
                                    target_groups[i].sub_groups.add(target_groups[j])
                            self.linked_groups.add(group_key)

                elif mode == "flow":
                    # Ищем ВСЕ группы этого потока (направление + год + форма + уровень)
                    target_groups = list(StudyGroup.objects.filter(**base_filter))
                    if not target_groups:
                        yield self._skip(idx, "Поток", "Не найдено ни одной группы для потока")
                        return

                # 3. СОЗДАНИЕ НАГРУЗКИ
                for g in target_groups:
                    _, created = AcademicLoad.objects.get_or_create(
                        semester=sem_obj,
                        discipline=d_obj,
                        lesson_type=lt_obj,
                        teacher=t_obj,
                        study_group=g,
                        whole_hours=hours,
                        whole_weeks=weeks,
                        defaults={"merge_key": m_key, "control_type":control}
                    )
                    if created:
                        self.load_created_counter += 1
                    else:
                        self.load_exists_counter += 1
                
                self.success_counter += 1

            except Exception as err:
                yield self._error(idx,err.__class__.__name__,str(err))


    def __iter__(self):
        # --- ПРОХОД 1: ВАЛИДАЦИЯ И ПОДГРУППЫ ---
        for idx, row in enumerate(self.data):
            # Валидация строки
            row_errors, norm = validate_load_row(row, idx)
            if row_errors:
                self.errors.extend(row_errors)
                self.skipped_counter += 1
                for msg in row_errors: yield msg
                continue

            # Определяем тип строки
            g_num = norm[16]      # group_num
            sub_g_num = norm[17]  # sub_group_num

            if g_num is None:
                # В очередь потоков
                self.queue_flow.append((idx, norm))
                continue
            
            if sub_g_num is None:
                # В очередь групп
                self.queue_groups.append((idx, norm))
                continue

            # Если мы здесь - это конкретная подгруппа (базовая единица)
            yield from self.process_row(idx, norm, mode="subgroup")

        # --- ПРОХОД 2: ОБРАБОТКА ГРУПП (уже есть все подгруппы) ---
        for idx, norm in self.queue_groups:
            yield from self.process_row(idx, norm, mode="group")

        # --- ПРОХОД 3: ОБРАБОТКА ПОТОКОВ (уже есть все группы) ---
        for idx, norm in self.queue_flow:
            yield from self.process_row(idx, norm, mode="flow")


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