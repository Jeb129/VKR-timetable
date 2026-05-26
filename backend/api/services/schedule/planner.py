import math
from collections import defaultdict
from django.db import transaction
from api.models import PlannedLesson

def make_base_key(load):
    return (
        load.semester_id,
        load.discipline_id,
        load.lesson_type_id,
        load.whole_hours,
        load.whole_weeks,
        load.merge_key,
    )

def make_group_key(load):
    sg = load.study_group
    lt = load.lesson_type

    # 1. Объединяем весь поток
    if lt.allow_merge_groups:
        return (
            "flow",
            (
                sg.study_program_id,
                sg.admission_year,
                sg.learning_form,
                sg.learning_stage,
            )
        )

    # 2. Объединяем все подгруппы в своей группе
    if lt.allow_merge_subgroups:
        return (
            "group",
            (
                sg.study_program_id,
                sg.admission_year,
                sg.learning_form,
                sg.learning_stage,
                sg.group_num,
            )
        )

    # 3. Не объединяем — подгруппа как есть
    return ("subgroup", sg.id)

def make_teacher_key(load):
    if load.discipline.allow_merge_teachers and load.lesson_type.allow_merge_teachers:
        return None
    return load.teacher_id

def make_final_key(load):
    return (
        make_base_key(load),
        make_group_key(load),
        make_teacher_key(load)
    )
def generate_planned_lessons_bulk(semester, loads):
    # 1. Группировка в памяти (используем ранее созданные функции make_final_key)
    buckets = defaultdict(list)
    for load in loads:
        key = make_final_key(load)
        buckets[key].append(load)

    planned_lessons_to_create = []
    
    # Вспомогательные списки для хранения данных, которые "приклеим" к объектам в памяти
    # так как у объектов в памяти еще нет id
    metadata = []

    # 2. Обработка бакетов в памяти
    for _, load_group in buckets.items():
        any_load = load_group[0]
        
        # Математика (плотность занятий)
        lessons_count = any_load.whole_hours / 2
        raw_density = (lessons_count / max(any_load.whole_weeks, 1)) * 2

        # lessons_in_cycle — это ПАРЫ в 2 недели. 
        # Не может быть больше общего кол-ва пар и не меньше 1 (если есть хоть 1 час)
        lessons_in_cycle = max(min(math.ceil(raw_density), math.ceil(lessons_count)), 1)

        # whole_weeks — за сколько недель вычитаем. 
        # Делим часы на "часы в неделю" (которых ровно lessons_in_cycle штук, т.к. пара=2ч, а цикл=2нед)
        calculated_weeks = math.ceil(any_load.whole_hours / lessons_in_cycle)

        # Создаем объект в памяти (без сохранения)
        pl = PlannedLesson(
            semester=semester,
            discipline=any_load.discipline,
            lesson_type=any_load.lesson_type,
            lessons_in_cycle=lessons_in_cycle,
            whole_weeks=calculated_weeks,
        )
        planned_lessons_to_create.append(pl)
        
        # Собираем уникальные ID для связей
        metadata.append({
            'teacher_ids': {l.teacher_id for l in load_group},
            'group_ids': {l.study_group_id for l in load_group},
            'load_ids': {l.id for l in load_group}
        })

    # 3. Сохранение в БД через одну транзакцию
    with transaction.atomic():
        # Очищаем старые плановые занятия для этого семестра
        PlannedLesson.objects.filter(semester=semester).delete()

        # Массовое создание PlannedLesson
        # bulk_create возвращает объекты с уже заполненными ID (в PostgreSQL это работает по умолчанию)
        created_objects = PlannedLesson.objects.bulk_create(planned_lessons_to_create)

        # Подготавливаем списки для промежуточных таблиц (M2M)
        PLTeacher = PlannedLesson.teachers.through
        PLGroup = PlannedLesson.study_groups.through
        PLLoad = PlannedLesson.academic_loads.through

        teachers_links = []
        groups_links = []
        loads_links = []

        for i, pl_obj in enumerate(created_objects):
            m = metadata[i]
            
            # Связи с преподавателями
            for t_id in m['teacher_ids']:
                teachers_links.append(PLTeacher(plannedlesson_id=pl_obj.id, teacher_id=t_id))
            
            # Связи с группами
            for g_id in m['group_ids']:
                groups_links.append(PLGroup(plannedlesson_id=pl_obj.id, studygroup_id=g_id))
            
            # Связи с исходной нагрузкой
            for l_id in m['load_ids']:
                loads_links.append(PLLoad(plannedlesson_id=pl_obj.id, academicload_id=l_id))

        # Массово вставляем связи
        PLTeacher.objects.bulk_create(teachers_links, batch_size=500)
        PLGroup.objects.bulk_create(groups_links, batch_size=500)
        PLLoad.objects.bulk_create(loads_links, batch_size=500)

    return len(created_objects)


def generate_planned_lessons_old(loads):
    buckets = defaultdict(list)

    # 1. Сгруппировать по ключу
    for load in loads:
        key = make_final_key(load)
        buckets[key].append(load)
    # 2. Построить черновики
    for _, load_group in buckets.items():
        any_load = load_group[0]

        lessons_count = any_load.whole_hours / 2
        weeks = lessons_count / max(any_load.whole_weeks,1)
        weeks_2 = math.ceil(weeks*2)
        whole_weeks =  math.ceil(any_load.whole_hours / max(weeks_2,1))

        draft, created = PlannedLesson.objects.get_or_create(
            semester = any_load.semester,
            discipline=any_load.discipline,
            lesson_type=any_load.lesson_type,
            lessons_in_cycle=weeks_2,
            whole_weeks=whole_weeks,
        )
        if created:
            for l in load_group:
                draft.study_groups.add(l.study_group)
                draft.teachers.add(l.teacher)
                draft.academic_loads.add(l)
    