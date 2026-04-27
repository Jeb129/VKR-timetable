import math
from dataclasses import dataclass, field
from collections import defaultdict
from typing import List, Set

@dataclass
class PlannedLessonDraft:
    discipline: object
    lesson_type: object

    groups: Set[object] = field(default_factory=set)
    teachers: Set[object] = field(default_factory=set)

    hours_per_two_weeks: int = 0
    weeks_total: int = 0

    loads: List[object] = field(default_factory=list)


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
                sg.group_num,
            )
        )

    # 3. Не объединяем — подгруппа как есть
    return ("subgroup", sg.id)

def make_teacher_key(load):
    return load.teacher_id

def make_final_key(load):
    return (
        make_base_key(load),
        make_group_key(load),
    )

def generate_planned_lessons(loads):
    buckets = defaultdict(list)

    # 1. Сгруппировать по ключу
    for load in loads:
        key = make_final_key(load)
        buckets[key].append(load)

    drafts = []

    # 2. Построить черновики
    for key, load_group in buckets.items():
        base_key, group_key = key
        any_load = load_group[0]

        draft = PlannedLessonDraft(
            discipline=any_load.discipline,
            lesson_type=any_load.lesson_type,
            hours_per_two_weeks=any_load.whole_hours * 2 /max(1,any_load.whole_weeks),
            weeks_total=any_load.whole_weeks,
        )

        for l in load_group:
            draft.groups.add(l.study_group)
            draft.teachers.add(l.teacher)
            draft.loads.append(l)

        drafts.append(draft)

    return drafts