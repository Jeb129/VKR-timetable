from api.services.constraints.meta import constraint, ConstraintError
from api.services.schedule.context import ScheduleContext

from api.models import (
    EquipmentRequirement,
    ClassroomPreference,
    ExcludedTimeslot,
    Lesson,
    enums,
)
from config.utils import get_cached_M2M


@constraint("room_meets_equipment_requirements")
def room_meets_equipment_requirements(
    lesson: Lesson, context: ScheduleContext, weight: int
):
    room = lesson.classroom
    if not room:
        return None

    req = context.requirements_cache[
        (lesson.discipline_id,lesson.lesson_type_id)
    ]
    provided = set(get_cached_M2M(room,"equipment"))
    missing = req - provided

    if missing:
        return ConstraintError(
            name="room_meets_equipment_requirements",
            message="Аудитория не соответствует требованиям по оснащению",
            penalty=weight * len(missing),
            data={"missing_equipment": missing, "room": room},
        )
    return None


@constraint("matches_teacher_room_preference")
def matches_teacher_room_preference(
    lesson: Lesson, context: ScheduleContext, weight: int
):
    room = lesson.classroom
    if not room:
        return None

    violations = []
    
    # Используем твою новую утилиту для получения учителей без SQL
    teachers = get_cached_M2M(lesson, 'teachers')

    for teacher in teachers:
        # Пытаемся найти предпочтение по ключу: (Учитель, Дисциплина, Тип занятия)
        pref_room = context.teacher_room_prefs.get(
            (teacher.id, lesson.discipline_id, lesson.lesson_type_id)
        )

        # Если предпочтение есть и оно не совпадает с текущей аудиторией
        if pref_room and pref_room.id != room.id:
            violations.append({
                "teacher": teacher, 
                "preferred_room": pref_room
            })

    return (
        ConstraintError(
            name="matches_teacher_room_preference",
            message="Выбранная аудитория не соответствует пожеланиям преподавателей",
            penalty=weight,
            data=violations,
        )
        if violations
        else None
    )


@constraint("lessons_ordering")
def lessons_ordering(lesson: Lesson, context: ScheduleContext, weight: int):
    ts = lesson.timeslot
    if not ts:
        return None

    violations = []
    for group in get_cached_M2M(lesson, 'study_groups'):
        chain = context.get_group_day_chain(group.id, ts.week_num, ts.day)
        # Проверяем порядок приоритетов в цепочке
        for i in range(len(chain) - 1):
            if chain[i].priority < chain[i + 1].priority:
                violations.append(
                    {
                        "group": group,
                        "early_lesson": chain[i],
                        "later_lesson": chain[i + 1],
                        "priorities": (chain[i].priority, chain[i + 1].priority),
                    }
                )
    return (
        ConstraintError(
            name="lessons_ordering",
            message="Занятия для группы стоят в неправильном порядке",
            penalty=weight,
            data=violations,
        )
        if violations
        else None
    )


@constraint("matches_teacher_time_preference")
def matches_teacher_time_preference(
    lesson: Lesson, context: ScheduleContext, weight: int
):
    ts = lesson.timeslot
    if not ts:
        return None

    violations = []
    for teacher in get_cached_M2M(lesson, 'teachers'):
        if (teacher.id, ts.id) in context.teacher_excluded_slots:
            violations.append({
                "teacher": teacher, 
                "timeslot": ts
            })

    return (
        ConstraintError(
            name="matches_teacher_time_preference",
            message="Выбранное время нежелательно для преподавателя",
            penalty=weight,
            data=violations,
        )
        if violations
        else None
    )
