from api.services.constraints.meta import constraint, ConstraintError
from api.services.schedule.context import ScheduleContext

from api.models import (
    EquipmentRequirement,
    ClassroomPreference,
    ExcludedTimeslot,
    Lesson,
    enums,
)


@constraint("room_meets_equipment_requirements")
def room_meets_equipment_requirements(
    lesson: Lesson, context: ScheduleContext, weight: int
):
    room = lesson.classroom
    if not room:
        return None

    req_ids = list(
        EquipmentRequirement.objects.filter(
            discipline=lesson.discipline, lesson_type=lesson.lesson_type
        )
    )

    if not req_ids:
        return None
    provided = set(room.equipment)
    missing = [rid for rid in req_ids if rid not in provided]

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
    for teacher in lesson.teachers.all():
        pref = ClassroomPreference.objects.filter(
            teacher=teacher,
            discipline=lesson.discipline,
            lesson_type=lesson.lesson_type,
            status=enums.RequestStatus.VERIFIED,
        ).first()
        if pref and pref.classroom_id != room.id:
            violations.append({"teacher": teacher, "preferred_room": pref.classroom})

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
    for group in lesson.study_groups.all():
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
    for teacher in lesson.teachers.all():
        if ExcludedTimeslot.objects.filter(
            teacher=teacher, timeslot=ts, status=enums.RequestStatus.VERIFIED
        ).exists():
            violations.append({"teacher": teacher, "timeslot": ts})

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
