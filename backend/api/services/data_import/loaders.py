import logging

from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.db.models import Q


from api.models import *
from api.services.data_import.excel import export_excel
from api.services.data_import.structure import ACADEMIC_LOAD_STRUCTURE, ACADEMIC_LOAD_STRUCTURE_TEST
from api.services.schedule.mapper import get_semester_by_date

logger = logging.getLogger("data_import")

def import_loading(data):
    errors = {}
    warnings = {}
    # Счетчики - Обработка строк
    skipped_counter = 0 # Пропущенные строки
    error_counter = 0 # Строки с необработанными ошибками
    success_counter = 0 # Успешно обработанные строки
    
    # Счетчики - загружаемые объекты
    programs_created_counter = 0 # Созданные направления подготовки
    programs_exists_counter = 0 # Уже существующие направления подготовки

    discipline_created_counter = 0 # Созданные дисциплины
    discipline_exists_counter = 0 # Уже существующие дисциплины

    teachers_created_counter = 0 # Созданные преподаватели
    teachers_exists_counter = 0 # Существующие преподаватели

    groups_created_counter = 0 # Созданные группы
    groups_exists_counter = 0 # Существующие группы

    load_created_counter = 0 # Созданные записи нагрузки
    load_exists_counter = 0 # Существующие записис нагрузки

    # Временные хранилища (чтобы не дергать БД каждый раз)

    programs = {}     # code -> {code, name, institute}
    teachers = {}     # fio -> {name, post}
    disciplines = {}
    groups = {}

    groups_raw = {} # Группы без подгруппы, для постобработки
    load_raw = [] # Академическая нагрузка для групп без подгрупп
    
    # Работаем со структурой ACADEMIC_LOAD_STRUCTURE из api\services\data_import\structure.py
    for idx, row in enumerate(data):

        # Загружаемые поля
        institute_short_name = row[0]
        study_program_code = row[1]
        study_program_name = row[2]
        study_program_short_name = row[3]

        discipline_name = row[4]
        d_allow_merge_teachers = row[5]

        lesson_type_name = row[6]
        lesson_type_short_name = row[7]

        semester_order= row[8]
        control_type = row[9]
        weeks = row[10]
        hours = row[11]

        teacher_institute_short_name = row[12]
        teacher_name = row[13]
        teacher_post = row[14]

        admission_year = row[15]
        group_num = row[16]
        sub_group_num = row[17]
        learning_form = row[18]
        learning_stage = row[19]
        students_count = row[20]

        # Валидация полей
        if not institute_short_name:
            msg = "Строка : Не заполнен институт"
            logger.debug(msg)
            skipped_counter += 1
            continue

        if not study_program_code:
            msg = f"Строка {idx}: Не заполнен код направления подготовки"
            logger.debug(msg)
            skipped_counter += 1
            continue

        if not study_program_name:
            msg = f"Строка {idx}: Не заполнено наименования направления подготовки"
            logger.debug(msg)
            skipped_counter += 1
            continue
        
        if not discipline_name:
            msg = f"Строка {idx}: Не заполнено наименование дисциплины"
            logger.debug(msg)
            skipped_counter += 1
            continue
        
        if not discipline_name:
            msg = f"Строка {idx}: Не заполнено наименование дисциплины"
            logger.debug(msg)
            skipped_counter += 1
            continue
        
        if not (lesson_type_name or lesson_type_short_name):
            msg = f"Строка {idx}: Не заполнен вид занятия"
            logger.debug(msg)
            skipped_counter += 1
            continue

        if not semester_order:
            msg = f"Строка {idx}: Не заполнен номер семестра или он равен 0"
            logger.debug(msg)
            skipped_counter += 1
            continue
        
        if not teacher_name:
            msg = f"Строка {idx}: Не заполнено имя преподавателя"
            logger.debug(msg)
            skipped_counter += 1
            continue
        
        if not teacher_institute_short_name:
            msg = f"Строка {idx}: Не заполнен минститут для преподавателя. Привязка данных может быть неточной"
            logger.debug(msg)

        if not admission_year:
            msg = f"Строка {idx}: Не заполнен год поступления группы"
            logger.debug(msg)
            skipped_counter += 1
            continue

        if not group_num:
            msg = f"Строка {idx}: Не заполнен номер группы"
            logger.debug(msg)
            skipped_counter += 1
            continue

        if not learning_form:
            msg = f"Строка {idx}: Не заполна форма обучения группы"
            logger.debug(msg)
            skipped_counter += 1
            continue

        if not learning_stage:
            msg = f"Строка {idx}: Не заполнен уровень образования группы"
            logger.debug(msg)
            skipped_counter += 1
            continue


        # Обработка строки
        with transaction.atomic():
            try:
                # Направление подготовки
                if study_program_code not in programs:
                    institute_obj = Institute.objects.filter(
                    short_name=institute_short_name
                    ).first()
                    if not institute_obj:
                        msg = f"Строка {idx}: Не найден институт {institute_short_name}"
                        logger.debug(msg)
                        skipped_counter += 1
                        continue

                    study_program_obj, created = StudyProgram.objects.get_or_create(
                            institute=institute_obj,
                            code=study_program_code,
                            defaults={
                                "name": study_program_name, 
                                "short_name": study_program_short_name
                                },
                        )
                    
                    programs[study_program_code] = study_program_obj
                    if created:
                        programs_created_counter += 1
                    else:
                        programs_exists_counter += 1
                else:
                    study_program_obj = programs[study_program_code]

                # Дисциплина
                if discipline_name not in disciplines:
                    discipline_obj, created = Discipline.objects.get_or_create(
                        name=discipline_name,
                        defaults={
                            "allow_merge_teachers": d_allow_merge_teachers
                            }
                        )
                    disciplines[discipline_name] = discipline_obj
                    if created:
                        discipline_created_counter += 1
                    else:
                        discipline_exists_counter += 1
                else:
                    discipline_obj = disciplines[discipline_name]
                
                # Вид занятия
                lesson_type_obj = LessonType.objects.filter(
                    Q(name = lesson_type_name) | Q(short_name = lesson_type_short_name)
                ).first()
                if not lesson_type_obj:
                    msg = f"Строка {idx}: Не найден вид занятия {lesson_type_name}, {lesson_type_short_name}"
                    logger.debug(msg)
                    skipped_counter += 1
                    continue
                
                # Преподаватель
                if (teacher_institute_short_name,teacher_name) not in teachers:
                    if teacher_institute_short_name:
                        teacher_inst_obj = Institute.objects.filter(
                        short_name=teacher_institute_short_name
                        ).first()
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
                    teachers[(teacher_institute_short_name,teacher_name)] = teacher_obj
                    if created:
                        teachers_created_counter += 1
                    else:
                        teachers_exists_counter += 1
                else:
                    teacher_obj =  teachers[(teacher_institute_short_name,teacher_name)]
                
                # Семестр
                start_year = admission_year + (semester_order) // 2
                month = 3 if semester_order % 2 == 0 else 10

                dt = f"{start_year}-{month:02d}-01"
                semester_obj = get_semester_by_date(dt)
                if not semester_obj:
                        msg = f"Строка {idx}: Не найден семестр на дату {dt}"
                        logger.debug(msg)
                        skipped_counter += 1
                        continue
                
                # Нагрузка
                group_key = (study_program_code, 
                                 admission_year,
                                 group_num,
                                 learning_form,
                                 learning_stage,
                                 sub_group_num)
                if sub_group_num is None:
                    if group_key not in groups_raw:
                        g_obj = StudyGroup(
                                study_program=study_program_obj,
                                admission_year=admission_year,
                                group_num=group_num,
                                learning_form=learning_form,
                                learning_stage=learning_stage,
                                students_count=students_count)
                            
                        groups_raw[group_key] = g_obj
                    else:
                        g_obj = groups_raw[group_key]
                    
                    load_raw.append(
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
                    if group_key not in groups:
                        g_obj, created = StudyGroup.objects.get_or_create(
                                study_program=study_program_obj,
                                admission_year=admission_year,
                                group_num=group_num,
                                learning_form=learning_form,
                                learning_stage=learning_stage,
                                students_count=students_count,
                                sub_group_num=int(sub_group_num)
                            )
                        groups[group_key] = g_obj
                        if created:
                            groups_created_counter += 1
                        else:
                            groups_exists_counter += 1
                    else:
                        g_obj = groups[group_key]
                    _, created = AcademicLoad.objects.get_or_create(
                            semester=semester_obj,
                            discipline=discipline_obj,
                            lesson_type=lesson_type_obj,
                            teacher=teacher_obj,
                            study_group=g_obj,
                            control_type=control_type,
                            whole_hours=hours,
                            whole_weeks=weeks,
                    )
                    if created:
                        load_created_counter += 1
                    else:
                        load_exists_counter += 1
                success_counter += 1
            except Exception as err:
                msg = f"Ошибка при обработке строки {idx}: {err}"
                logger.debug(msg)
                error_counter += 1

        # Постобработка,для групп без номера подгруппы
        for _,raw_group in groups_raw.items():
            try:
                with transaction.atomic():
                    subs = list(StudyGroup.objects.filter(
                                admission_year = raw_group.admission_year,
                                study_program = raw_group.study_program,
                                learning_form = raw_group.learning_form,
                                learning_stage = raw_group.learning_stage,
                                group_num=raw_group.group_num,
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
                            group_num=raw_group.group_num,
                        )
                        if created:
                            groups_created_counter += 1
                        else:
                            groups_created_counter += 1
                        subs.append(group)
                        count += 1

                    academic_loads = [a for a in load_raw if (
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
                                whole_weeks =raw_load.whole_weeks
                                )
                            if created:
                                load_created_counter += 1
                            else:
                                load_exists_counter += 1                          
                        # Соединяем группы в подгруппы
                        for j in range(i+1,count):
                            subs[i].sub_groups.add(subs[j])
            except Exception as err:
                msg = f"Ошибка при постобработке группы {raw_group}: {err}"
                logger.debug(msg)
                error_counter+=1
        info_msg = (
            f"Успешно обработано строк {success_counter}\n" +
            f"Пропущено строк {skipped_counter}\n" +
            f"Строк с ошибками {error_counter}\n"
        )                    
        created_msg = (
            f"Создано направлений подгатовки: {programs_created_counter}\n" + 
            f"Сщздано учебных групп: {groups_created_counter}\n" + 
            f"Создано преподавателей: {teachers_created_counter}\n" + 
            f"Создано записей нагрузки: {load_created_counter}\n"
            )
        exists_msg = (
            f"Найдено существующих направлений подгатовки: {programs_exists_counter}\n" + 
            f"Найдено существующих  учебных групп: {groups_exists_counter}\n" + 
            f"Найдено существующих  преподавателей: {teachers_exists_counter}\n" + 
            f"Найдено существующих  записей нагрузки: {load_exists_counter}\n"
        )

        return info_msg, created_msg, exists_msg

def export_loading(queryset = None):
    now = timezone.now()
    path = settings.BASE_DIR / "data_exports" / f"Нагрузка_{now.date()}.xlsx"
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

        # --- вычисление номера семестра ---
        sem_order = 1 if load.semester.date_start.month < 7 else 0
        sem_year = load.semester.date_start.year - load.study_group.admission_year
        sem_num = sem_year*2 - sem_order + 1

        # Расчет семестра Осень 2022 для 22-ИСбо-1
        # sem_order = 0 (сентябрь 9 месяц)
        # sem_year = 2022 - 2022  = 0
        # sem = 0 * 2 - 0 + 1 = 1

        # Расчет семестра Весна 2023 для 22-ИСбо-1
        # sem_order = 1 (январь 1 месяц)
        # sem_year = 2023 - 2022  = 1
        # sem = 1 * 2 - 1 + 1 = 8

        # Расчет семестра Осень 2025 для 22-ИСбо-1
        # sem_order = 0 (сентябрь 9 месяц)
        # sem_year = 2025 - 2022  = 3
        # sem = 3 * 2 - 0 + 1 = 7

        # Расчет семестра Весна 2026 для 22-ИСбо-1
        # sem_order = 1 (январь 1 месяц)
        # sem_year = 2026 - 2022  = 4
        # sem = 4 * 2 - 1 + 1 = 8

        if sem_num == 0:
            print(f"""
Расчет семестра {load.semester} для {group.name}
sem_order = {sem_order} ({load.semester.date_start.month})
sem_year = {load.semester.date_start.year} - {load.study_group.admission_year}
sem_num = {sem_year}*2 - {sem_order} + 1
""")

        row = [
            load.id,
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
            load.lesson_type.allow_merge_teachers,
            load.lesson_type.allow_merge_subgroups,
            load.lesson_type.allow_merge_groups,

            # Нагрузка
            sem_num,
            load.control_type,
            load.whole_weeks,
            load.whole_hours,

            # Преподаватель
            load.teacher.name,
            load.teacher.post,

            # Группа
            group.admission_year,
            group.group_num,
            group.sub_group_num,
            group.learning_form,
            group.learning_stage,
            group.students_count,
        ]

        data.append(row)

    export_excel(path, data, ACADEMIC_LOAD_STRUCTURE_TEST)