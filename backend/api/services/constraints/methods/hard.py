from django.db.models import Q
from api.services.constraints.meta import constraint, ConstraintError
from api.services.schedule.context import ScheduleContext
from api.models import (
    BuildingTravelTime,
    Lesson,
)


@constraint("teacher_no_overlap")
def teacher_no_overlap(lesson: Lesson, context: ScheduleContext, weight: int):
    ts = lesson.timeslot
    if not ts:
        return None

    violations = []
    for teacher in lesson.teachers.all():
        others = context.teacher_lookup.get((teacher.id, ts.id), [])
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
    ts = lesson.timeslot
    if not ts:
        return None

    violations = []
    for group in lesson.study_groups.all():
        others = context.group_lookup.get((group.id, ts.id), [])
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
    if not ts or not room or room.allow_parallel:
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

    total_students = sum(g.students_count for g in lesson.study_groups.all())
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
    # Проверяем перемещения для учителей и групп
    entities_to_check = [
        ("teacher", lesson.teachers.all()),
        ("group", lesson.study_groups.all()),
    ]

    for type_name, entities in entities_to_check:
        for ent in entities:
            prev_l, next_l = (
                context.get_teacher_neighbors(lesson, ent.id)
                if type_name == "teacher"
                else context.get_group_neighbors(lesson, ent.id)
            )

            for neighbor in filter(None, [prev_l, next_l]):
                if not neighbor.classroom or neighbor.classroom.is_virtual:
                    continue
                if room.building_id == neighbor.classroom.building_id:
                    continue

                travel = BuildingTravelTime.objects.filter(
                    (
                        Q(from_building_id=room.building_id)
                        & Q(to_building_id=neighbor.classroom.building_id)
                    )
                    | (
                        Q(from_building_id=neighbor.classroom.building_id)
                        & Q(to_building_id=room.building_id)
                    )
                ).first()

                travel_min = travel.travel_time_minutes if travel else 999
                # Время между концом одной и началом другой
                available = abs(
                    (ts.time_start.hour * 60 + ts.time_start.minute)
                    - (
                        neighbor.timeslot.time_end.hour * 60
                        + neighbor.timeslot.time_end.minute
                    )
                )

                if travel_min > available:
                    violations.append(
                        {
                            "entity": ent,
                            "type": type_name,
                            "travel_time": travel_min,
                            "available_time": available,
                            "neighbor_lesson": neighbor,
                        }
                    )
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
