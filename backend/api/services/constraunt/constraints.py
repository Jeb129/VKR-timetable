from django.db.models import Q
from api.services.constraunt.meta import constraint, ConstraintError
from .context import ScheduleContext
from api.models import (
    EquipmentRequirement,
    BuildingTravelTime,
    ClassroomPreference,
    ExcludedTimeslot,
    Lesson,
    enums
)
#               Описание                    Вес    Имя метода для проверки
# ---------------------------------------Жёсткие---------------------------------------
# Пересечение по преподавателю	            500    teacher_no_overlap
# Пересечение по группе	                    500    group_no_overlap
# Пересечение по аудиториям	                500	   room_no_overlap
# Аудитория вмещает всех студентов          500	   room_has_enough_seats
# Невозможность перехода между корпусами    500	   building_travel_impossible
# 
# ---------------------------------Техника / приоритет---------------------------------
# Аудитория соответствует оборудованию      400	   room_meets_equipment_requirements
# Предпочтения преподавателя по аудитории	300    matches_teacher_room_preference
# Ручной приоритет (упорядочивание)	        300    lessons_ordering
# Предпочтения преподавателя по времени	    200	   matches_teacher_time_preference
# 
# --------------------------------Эргономика / качество--------------------------------
# Дневная перегрузка группы	                150	   group_daily_overload
# Дневная перегрузка преподавателя	        100	   teacher_daily_overload
# Окно у студентов	                        100	   students_gap
# Факт смены корпуса в течение дня	        100	   building_clustering
# Позиционирование временных занятий	    100	   lesson_persistence_sort
# Приоритет заполнения первой половины дня	80	   morning_preference
# Окно у преподавателя	                    50	   teachers_gap
# Недельная перегрузка преподавателя	    50	   teacher_weekly_overload
# Недельная перегрузка группы	            50	   group_weekly_overload


# =============================================================================
# ЖЕСТКИЕ ОГРАНИЧЕНИЯ
# =============================================================================

@constraint("teacher_no_overlap", isHard=True)
def teacher_no_overlap(lesson:Lesson, context: ScheduleContext, weight: int):
    ts = lesson.timeslot
    if not ts: return None
    
    violations = []
    for teacher in lesson.teachers.all():
        others = context.teacher_lookup.get((teacher.id, ts.id), [])
        for other in others:
            if other.id != lesson.id:
                violations.append({
                    "teacher": teacher,
                    "lesson": other
                })
    return ConstraintError(name="teacher_no_overlap", penalty=weight, data=violations) if violations else None


@constraint("group_no_overlap", isHard=True)
def group_no_overlap(lesson:Lesson, context: ScheduleContext, weight: int):
    ts = lesson.timeslot
    if not ts: return None
    
    violations = []
    for group in lesson.study_groups.all():
        others = context.group_lookup.get((group.id, ts.id), [])
        for other in others:
            if other.id != lesson.id:
                violations.append({
                    "group": group,
                    "lesson": other
                })
    return ConstraintError(name="group_no_overlap", penalty=weight, data=violations) if violations else None


@constraint("room_no_overlap", isHard=True)
def room_no_overlap(lesson:Lesson, context: ScheduleContext, weight: int):
    ts = lesson.timeslot
    room = lesson.classroom
    if not ts or not room or room.allow_parallel: return None
    
    others = [other for other in context.classroom_lookup.get((room.id, ts.id), []) if other.id != lesson.id]
    if others:
        return ConstraintError(
            name="room_no_overlap",
            penalty=weight,
            data=[{"room": room, "lesson": other} for other in others]
        )
    return None


@constraint("room_has_enough_seats", isHard=True)
def room_has_enough_seats(lesson:Lesson, context: ScheduleContext, weight: int):
    room = lesson.classroom
    if not room or room.is_virtual: return None
    
    total_students = sum(g.students_count for g in lesson.study_groups.all())
    if total_students > room.capacity:
        return ConstraintError(
            name="room_has_enough_seats",
            penalty=weight,
            message=f"Требуется {total_students} мест, в наличии {room.capacity}",
            data={"required": total_students, "capacity": room.capacity, "room": room}
        )
    return None


@constraint("building_travel_impossible", isHard=True)
def building_travel_impossible(lesson:Lesson, context: ScheduleContext, weight: int):
    ts = lesson.timeslot
    room = lesson.classroom
    if not ts or not room or room.is_virtual: return None

    violations = []
    # Проверяем перемещения для учителей и групп
    entities_to_check = [('teacher', lesson.teachers.all()), ('group', lesson.study_groups.all())]

    for type_name, entities in entities_to_check:
        for ent in entities:
            prev_l, next_l = (context.get_teacher_neighbors(lesson, ent.id) if type_name == 'teacher' 
                              else context.get_group_neighbors(lesson, ent.id))
            
            for neighbor in filter(None, [prev_l, next_l]):
                if not neighbor.classroom or neighbor.classroom.is_virtual: continue
                if room.building_id == neighbor.classroom.building_id: continue

                travel = BuildingTravelTime.objects.filter(
                    (Q(from_building_id=room.building_id) & Q(to_building_id=neighbor.classroom.building_id)) |
                    (Q(from_building_id=neighbor.classroom.building_id) & Q(to_building_id=room.building_id))
                ).first()
                
                travel_min = travel.travel_time_minutes if travel else 999
                # Время между концом одной и началом другой
                available = abs((ts.time_start.hour * 60 + ts.time_start.minute) - 
                                (neighbor.timeslot.time_end.hour * 60 + neighbor.timeslot.time_end.minute))

                if travel_min > available:
                    violations.append({
                        "entity": ent,
                        "type": type_name,
                        "travel_time": travel_min,
                        "available_time": available,
                        "neighbor_lesson": neighbor
                    })
    return ConstraintError(name="building_travel_impossible", penalty=weight, data=violations) if violations else None


# =============================================================================
# ТЕХНИКА / ПРИОРИТЕТ
# =============================================================================

@constraint("room_meets_equipment_requirements")
def room_meets_equipment_requirements(lesson:Lesson, context: ScheduleContext, weight: int):
    room = lesson.classroom
    if not room: return None
    
    req_ids = list(EquipmentRequirement.objects.filter(
        discipline=lesson.discipline, lesson_type=lesson.lesson_type
    ).values_list('equipment_id', flat=True))
    
    if not req_ids: return None
    provided_ids = set(room.equipment.values_list('id', flat=True))
    missing_ids = [rid for rid in req_ids if rid not in provided_ids]

    if missing_ids:
        return ConstraintError(
            name="room_meets_equipment_requirements",
            penalty=weight * len(missing_ids),
            data={"missing_equipment_ids": missing_ids, "room": room}
        )
    return None


@constraint("matches_teacher_room_preference")
def matches_teacher_room_preference(lesson:Lesson, context: ScheduleContext, weight: int):
    room = lesson.classroom
    if not room: return None
    
    violations = []
    for teacher in lesson.teachers.all():
        pref = ClassroomPreference.objects.filter(
            teacher=teacher, discipline=lesson.discipline, 
            lesson_type=lesson.lesson_type, status=enums.RequestStatus.VERIFIED
        ).first()
        if pref and pref.classroom_id != room.id:
            violations.append({"teacher": teacher, "preferred_room": pref.classroom})
            
    return ConstraintError(name="matches_teacher_room_preference", penalty=weight, data=violations) if violations else None


@constraint("lessons_ordering")
def lessons_ordering(lesson:Lesson, context: ScheduleContext, weight: int):
    ts = lesson.timeslot
    if not ts: return None
    
    violations = []
    for group in lesson.study_groups.all():
        chain = context.get_group_day_chain(group.id, ts.week_num, ts.day)
        # Проверяем порядок приоритетов в цепочке
        for i in range(len(chain) - 1):
            if chain[i].priority < chain[i+1].priority:
                violations.append({
                    "group": group,
                    "early_lesson": chain[i],
                    "later_lesson": chain[i+1],
                    "priorities": (chain[i].priority, chain[i+1].priority)
                })
    return ConstraintError(name="lessons_ordering", penalty=weight, data=violations) if violations else None


@constraint("matches_teacher_time_preference")
def matches_teacher_time_preference(lesson:Lesson, context: ScheduleContext, weight: int):
    ts = lesson.timeslot
    if not ts: return None
    
    violations = []
    for teacher in lesson.teachers.all():
        if ExcludedTimeslot.objects.filter(teacher=teacher, timeslot=ts, status=enums.RequestStatus.VERIFIED).exists():
            violations.append({"teacher": teacher, "timeslot": ts})
            
    return ConstraintError(name="matches_teacher_time_preference", penalty=weight, data=violations) if violations else None


# =============================================================================
# ЭРГОНОМИКА / КАЧЕСТВО
# =============================================================================

@constraint("group_daily_overload")
def group_daily_overload(lesson:Lesson, context: ScheduleContext, weight: int):
    ts = lesson.timeslot
    if not ts: return None
    
    violations = []
    for group in lesson.study_groups.all():
        chain = context.get_group_day_chain(group.id, ts.week_num, ts.day)
        hours = len(chain) * 2
        limit = getattr(group, 'max_hours_per_day', 8) or 8
        if hours > limit:
            violations.append({"group": group, "current_hours": hours, "limit": limit})
            
    return ConstraintError(name="group_daily_overload", penalty=weight, data=violations) if violations else None


@constraint("teacher_daily_overload")
def teacher_daily_overload(lesson:Lesson, context: ScheduleContext, weight: int):
    ts = lesson.timeslot
    if not ts: return None
    
    violations = []
    for teacher in lesson.teachers.all():
        chain = context.get_teacher_day_chain(teacher.id, ts.week_num, ts.day)
        hours = len(chain) * 2
        limit = teacher.max_hours_per_day or 8
        if hours > limit:
            violations.append({"teacher": teacher, "current_hours": hours, "limit": limit})
            
    return ConstraintError(name="teacher_daily_overload", penalty=weight, data=violations) if violations else None


@constraint("students_gap")
def students_gap(lesson:Lesson, context: ScheduleContext, weight: int):
    ts = lesson.timeslot
    if not ts: return None
    
    violations = []
    for group in lesson.study_groups.all():
        prev, nxt = context.get_group_neighbors(lesson, group.id)
        if prev and (ts.order_number - prev.timeslot.order_number > 1):
            violations.append({"group": group, "side": "before", "gap_with": prev})
        if nxt and (nxt.timeslot.order_number - ts.order_number > 1):
            violations.append({"group": group, "side": "after", "gap_with": nxt})
            
    return ConstraintError(name="students_gap", penalty=weight * len(violations), data=violations) if violations else None


@constraint("building_clustering")
def building_clustering(lesson:Lesson, context: ScheduleContext, weight: int):
    ts = lesson.timeslot
    if not ts: return None
    
    violations = []
    for group in lesson.study_groups.all():
        chain = context.get_group_day_chain(group.id, ts.week_num, ts.day)
        buildings = {l.classroom.building for l in chain if l.classroom and not l.classroom.is_virtual}
        if len(buildings) > 1:
            violations.append({"group": group, "buildings": list(buildings)})
            
    return ConstraintError(name="building_clustering", penalty=weight * len(violations), data=violations) if violations else None


@constraint("lesson_persistence_sort")
def lesson_persistence_sort(lesson:Lesson, context: ScheduleContext, weight: int):
    ts = lesson.timeslot
    if not ts or not lesson.whole_weeks: return None
    
    # "Временные" занятия (напр. меньше 10 недель) в середине дня (2, 3, 4 пары)
    if lesson.whole_weeks < 10 and 1 < ts.order_number < 5:
        return ConstraintError(name="lesson_persistence_sort", penalty=weight, data={"weeks": lesson.whole_weeks, "order": ts.order_number})
    return None


@constraint("morning_preference")
def morning_preference(lesson:Lesson, context: ScheduleContext, weight: int):
    ts = lesson.timeslot
    if not ts or ts.order_number == 1: return None
    return ConstraintError(name="morning_preference", penalty=(ts.order_number - 1) * weight, data={"order": ts.order_number})


@constraint("teachers_gap")
def teachers_gap(lesson:Lesson, context: ScheduleContext, weight: int):
    ts = lesson.timeslot
    if not ts: return None
    
    violations = []
    for teacher in lesson.teachers.all():
        prev, nxt = context.get_teacher_neighbors(lesson, teacher.id)
        if prev and (ts.order_number - prev.timeslot.order_number > 1):
            violations.append({"teacher": teacher, "side": "before", "gap_with": prev})
        if nxt and (nxt.timeslot.order_number - ts.order_number > 1):
            violations.append({"teacher": teacher, "side": "after", "gap_with": nxt})
            
    return ConstraintError(name="teachers_gap", penalty=weight * len(violations), data=violations) if violations else None


@constraint("teacher_weekly_overload")
def teacher_weekly_overload(lesson:Lesson, context: ScheduleContext, weight: int):
    violations = []
    for teacher in lesson.teachers.all():
        hours = context.get_teacher_weekly_hours(teacher.id)
        limit = teacher.max_hours_per_week or 36
        if hours > limit:
            violations.append({"teacher": teacher, "hours": hours, "limit": limit})
            
    return ConstraintError(name="teacher_weekly_overload", penalty=weight, data=violations) if violations else None


@constraint("group_weekly_overload")
def group_weekly_overload(lesson:Lesson, context: ScheduleContext, weight: int):
    violations = []
    for group in lesson.study_groups.all():
        hours = context.get_group_weekly_hours(group.id)
        limit = getattr(group, 'max_hours_per_week', 36) or 36
        if hours > limit:
            violations.append({"group": group, "hours": hours, "limit": limit})
            
    return ConstraintError(name="group_weekly_overload", penalty=weight, data=violations) if violations else None