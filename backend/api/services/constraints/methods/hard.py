from api.services.constraints.meta import constraint, ConstraintError
from api.services.schedule.context import ScheduleContext
from api.models import Lesson
from config.utils import get_cached_M2M


@constraint("teacher_no_overlap")
def teacher_no_overlap(lesson: Lesson, context: ScheduleContext, weight: int):
    ts_id = lesson.timeslot.id
    if not ts_id:
        return None

    violations = []
    for teacher in get_cached_M2M(lesson,"teachers"):
        others = context.teacher_lookup.get((teacher.id, ts_id), [])
        for other in others:
            if other.id != lesson.id:
                violations.append({"teacher": teacher, "lesson": other})
    return (
        ConstraintError(
            name="teacher_no_overlap",
            message="Некоторые преподаватели заняты в это время",
            penalty=weight,
            data=violations,
        )
        if violations
        else None
    )


@constraint("group_no_overlap")
def group_no_overlap(lesson: Lesson, context: ScheduleContext, weight: int):
    ts_id = lesson.timeslot.id
    if not ts_id:
        return None

    violations = []
    for group in get_cached_M2M(lesson,"study_groups"):
        others = context.group_lookup.get((group.id, ts_id), [])
        for other in others:
            if other.id != lesson.id:
                violations.append({"group": group, "lesson": other})
    return (
        ConstraintError(
            name="group_no_overlap",
            message="Некоторые группы заняты в это время",
            penalty=weight,
            data=violations,
        )
        if violations
        else None
    )


@constraint("room_no_overlap")
def room_no_overlap(lesson: Lesson, context: ScheduleContext, weight: int):
    ts = lesson.timeslot
    room = lesson.classroom
    
    if not ts or not room:
        return None
    if room.allow_parallel:
        return None

    others = [
        other
        for other in context.classroom_lookup.get((room.id, ts.id), [])
        if other.id != lesson.id
    ]
    if others:
        return ConstraintError(
            name="room_no_overlap",
            message=f"Аудитория {room} занята в это время",
            penalty=weight,
            data=[{"room": room, "lesson": other} for other in others],
        )
    return None


@constraint("room_has_enough_seats")
def room_has_enough_seats(lesson: Lesson, context: ScheduleContext, weight: int):
    room = lesson.classroom
    if not room or room.is_virtual:
        return None

    total_students = getattr(lesson, 'total_students', None) or sum(g.students_count for g in lesson.study_groups.all())

    if total_students > room.capacity:
        return ConstraintError(
            name="room_has_enough_seats",
            penalty=weight,
            message=f"Требуется {total_students} мест, в наличии {room.capacity}",
            data={"required": total_students, "capacity": room.capacity, "room": room},
        )
    return None

@constraint("building_travel_impossible")
def building_travel_impossible(lesson: Lesson, context: ScheduleContext, weight: int):
    ts = lesson.timeslot
    room = lesson.classroom
    
    if not ts or not room or room.is_virtual:
        return None

    violations = []

    teachers = get_cached_M2M(lesson,"teachers")
    groups = get_cached_M2M(lesson,"study_groups")

    check_list = [("teacher", teachers), ("group", groups)]

    for type_name, entities in check_list:
        for ent in entities:
            # Получаем соседей из индекса контекста
            prev_l, next_l = (
                context.get_teacher_neighbors(lesson, ent.id)
                if type_name == "teacher"
                else context.get_group_neighbors(lesson, ent.id)
            )

            # Проверяем и предыдущее, и следующее занятие
            if prev_l:
                # Оцениваем перемещение с предыдущего на текущее
                err = _check_travel(prev_l, lesson, context, "prev")
                if err: violations.append({**err, "entity": ent, "type": type_name})
            
            if next_l:
                # Оцениваем перемещение с текущего на следующее
                err = _check_travel(lesson, next_l, context, "next")
                if err: violations.append({**err, "entity": ent, "type": type_name})

    return (
        ConstraintError(
            name="building_travel_impossible",
            message="Недостаточно времени для перехода",
            penalty=weight,
            data=violations,
        )
        if violations
        else None
    )

def _check_travel(l1: Lesson, l2: Lesson, context: ScheduleContext, direction):
    """
    Вспомогательная функция для проверки пары занятий.
    Работает БЕЗ обращений к БД.
    """
    # Если аудитории нет или она виртуальная — перемещение всегда возможно
    r1, r2 = l1.classroom, l2.classroom
    if not r1 or not r2 or r1.is_virtual or r2.is_virtual:
        return None
    
    b1_id, b2_id = r1.building_id, r2.building_id
    if b1_id == b2_id:
        return None

    # Ищем время перемещения в кэше. Если нет в базе - считаем очень далеким (999)
    travel_min = context.travel_map.get((b1_id, b2_id), 999)
    
    # Берем время из кэша слотов
    _, t1_end = context.slot_times.get(l1.timeslot_id, (0,0))
    t2_start, _ = context.slot_times.get(l2.timeslot_id, (0,0))

    available = t2_start - t1_end
    
    if travel_min > available:
        return {
            "travel_time": travel_min,
            "available_time": available,
            "neighbor_lesson": l1 if direction == "prev" else l2,
        }
    return None