import math
from collections import defaultdict

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

def generate_planned_lessons(loads):
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
    