from dataclasses import dataclass
import logging
import os
from turtle import reset
from typing import Any, List
from django.db.models import Q

from api.models.models import AcademicLoad, BuildingTravelTime, ClassroomPreference, Constraint, ExcludedTimeslot, Lesson
from backend.api.models.enums import RequestStatus

logger = logging.getLogger("constraints")

registry = {}
def constraint(name):
    """Регистрирует функцию проверки под именем ограничения."""
    def decorator(func):
        registry[name] = func
        return func
    return decorator

# constraints = [
#     ("Пересечение по преподавателю", 500, "teacher_no_overlap"),
#     ("Пересечение по группе", 500, "group_no_overlap"),
#     ("Пересечение по аудиториям", 500, "room_no_overlap"),
#     ("Аудитория вмещает всех студентов", 500, "room_has_enough_seats"),
#     ("Аудитория соответствует оборудованию", 400, "room_meets_equipment_requirements"),
#     ("Предпочтения преподавателя по аудитории", 300, "matches_teacher_room_preference"),
#     ("Предпочтения преподавателя по времени", 200, "matches_teacher_time_preference"),
#     ("Переход между корпусами", 500, "building_change"),
#     ("Окно у студентов", 100, "students_gap"),
#     ("Окно у преподавателя", 50, "teachers_gap"), # Тоже важно, оказывается, но парвда окно у препода побольше
#     ("Перегрузка преподователя",50,"teacher_overload")
# ]
@dataclass
class ConstraintError ():
    name: str
    penalty: int = 0
    message: str = "OK"
    data: Any = None # По идее сюда можно запихнуть что угодно, например занятия, с которыми возникает ошибка

class ConstraintManager():
    '''Сессия проверки расписания Проверяет ограничения из бд и проверяет есть ли его реализация'''
   
    def __init__(self):
        self.constraints: List[Constraint] = []
        self.methods = {}  
   
    def load(self):
        """Загружает ограничения и сопоставляет с реализованными функциями."""
        logger.info("Проверка реализации ограничений ограничений")

        for c in Constraint.objects.all():
            func = registry.get(c.name)
            if func is None:
                logger.warning(f"Ограничение '{c.name}' не реализовано.")
                continue

            self.constraints.append(c)
            self.methods[c.name] = func

    def check_lesson(self, lesson: Lesson):
            """Проверяет одно занятие всеми реализованными ограничениями."""
            results = []

            for c in self.constraints:
                func = self.methods.get(c.name)
                if func is None:
                    continue

                result = func(lesson, weight=c.weight)
                if result:
                    results.append(result)

            return results

    def check_scenario(self, scenario):
        """Проверяет всё расписание."""
        errors = []
        for lesson in scenario.lessons.all():
            errors.extend(self.check_lesson(lesson))
        return errors
 

@constraint("teacher_no_overlap")
def teacher_no_overlap(lesson: Lesson, weight):
    teacher_ids = lesson.teachers.values_list("id", flat=True)
    slot = lesson.timeslot

    conflicts = (
        Lesson.objects
        .filter(scenario__id=lesson.scenario.id)
        .filter(timeslot=slot)
        .filter(teachers__id__in=teacher_ids)
        .exclude(id=lesson.id) # type: ignore
        .distinct()
    )

    # нет конфликтов → возвращаем "пустую" ошибку
    if not conflicts.exists():
        return ConstraintError(name="teacher_no_overlap")

    conflict_entries = []

    # Ограничение жесткое, но на всякий добавил расчет от веса ограничений в преподавателе
    penalties = []

    for conf in conflicts:
        common_teachers = conf.teachers.filter(id__in=teacher_ids)
        max_teacher_weight = max(t.weight for t in common_teachers)

        penalties.append(weight * max_teacher_weight)

        conflict_entries.append({
            "lesson": conf,
            "teachers": common_teachers,
        })

    final_penalty = max(penalties)

    return ConstraintError(
        name="teacher_no_overlap",
        penalty=final_penalty,
        message="Преподаватель занят в это время",
        data={
            "conflicts": conflict_entries
        }
    )

@constraint("group_no_overlap")
def group_no_overlap(lesson: Lesson, weight):
    groups_ids = lesson.study_groups.values_list("id", flat=True)
    slot = lesson.timeslot

    conflicts = (
        Lesson.objects
        .filter(scenario__id=lesson.scenario.id)
        .filter(timeslot=slot)
        .filter(groups__id__in=groups_ids)
        .exclude(id=lesson.id) # type: ignore
        .distinct()
    )

    # нет конфликтов → возвращаем "пустую" ошибку
    if not conflicts.exists():
        return ConstraintError(name="group_no_overlap")

    conflict_entries = []
    for conf in conflicts:
        common_groups = list(conf.study_groups.filter(id__in=groups_ids))

        conflict_entries.append({
            "lesson": conf,
            "groups": common_groups,
        })

    return ConstraintError(
        name="group_no_overlap",
        penalty=weight,
        message="Группы заняты в это время",
        data={
            "conflicts": conflict_entries
        }
    )

@constraint("room_no_overlap")
def room_no_overlap(lesson: Lesson, weight):
    room_id = lesson.classroom.id # type: ignore
    slot = lesson.timeslot

    conflicts = (
        Lesson.objects
        .filter(scenario__id=lesson.scenario.id)
        .filter(timeslot=slot)
        .filter(classroom__id=room_id)
        .exclude(id=lesson.id) # type: ignore
        .distinct()
    )
    if not conflicts.exists():
        return ConstraintError(name="room_no_overlap")
    
    return ConstraintError(
        name="room_no_overlap",
        penalty=weight,
        message="Аудитория занята в это время",
        data={
            "conflicts": conflicts
        }
    )

@constraint("room_has_enough_seats")
def room_has_enough_seats(lesson:Lesson, weight):
    classroom = lesson.classroom
    if not classroom:
        return ConstraintError( name="classroom_capacity" )
    
    capacity = classroom.capacity
    groups = lesson.study_groups.all()
    total_students = sum(g.students_count for g in groups)

    if total_students <= total_students:
        return ConstraintError( name="classroom_capacity" )
    
    overflow = total_students - capacity

    return ConstraintError(
        name="classroom_capacity",
        penalty=weight * overflow,
        message=f"Аудиторияя {classroom} не может вместить {total_students} чел. (вместимость аудитории {capacity} чел.)",
        data={
            "classroom": classroom,
            "capacity": capacity,
            "total_students": total_students,
            "overflow": overflow,
        }
    )

@constraint("room_meets_equipment_requirements")
def room_meets_equipment_requirements(lesson: Lesson, *, weight) -> ConstraintError:
    


    # Аудитория занятия
    classroom = lesson.classroom

    if not classroom:
        # Если аудитория отсутствует — нарушение по умолчанию,
        # так как невозможно проверить соответствие
        return ConstraintError(
            name="room_meets_equipment_requirements",
            penalty=weight,
            message="У занятия не назначена аудитория",
        )
    
    academic_load = (AcademicLoad.objects
                    .filter(discipline__id=lesson.discipline.id)# type: ignore
                    .filter(lesson_type=lesson.lesson_type)
                ) 

    # Требуемое оборудование
    required = list(academic_load.required_equipment.all())

    # Оборудование аудитории
    provided = list(classroom.equipment.all())

    # Множество id для быстрого сравнения
    required_ids = {e.id for e in required}
    provided_ids = {e.id for e in provided}

    # Что отсутствует
    missing_ids = required_ids - provided_ids

    if not missing_ids:
        return ConstraintError(
            name="equipment_required",
            penalty=0,
            message="OK",
            data=None,
        )

    missing = [e for e in required if e.id in missing_ids]

    # Можно сделать штраф = weight * количество отсутствующего оборудования
    penalty = weight * len(missing)

    return ConstraintError(
        name="equipment_required",
        penalty=penalty,
        message="В аудитории отсутствует необходимое оборудование",
        data={
            "lesson": lesson,
            "classroom": classroom,
            "required_equipment": required,
            "provided_equipment": provided,
            "missing_equipment": missing,
        }
    )

@constraint("matches_teacher_room_preference")
def matches_teacher_room_preference(lesson: Lesson, *, weight) -> ConstraintError:

    classroom = lesson.classroom
    teachers = list(lesson.teachers.all())

    # дисциплина и тип занятия у урока
    discipline = lesson.discipline
    lesson_type = lesson.lesson_type

    # Накопление нарушений, если преподавателей несколько
    violations = []

    for t in teachers:

        # Находим preferences преподавателя по конкретной дисциплине и типу занятия
        prefs = ClassroomPreference.objects.filter(
            teacher=t,
            discipline=discipline,
            lesson_type=lesson_type,
            status=RequestStatus.VERIFIED
        )

        if not prefs.exists():
            # У преподавателя нет предпочтений для этой пары — всё ок
            continue

        # Если предпочтений несколько — это редкость, но возможна ситуация
        for p in prefs:
            preferred_classroom = p.classroom

            if preferred_classroom.id != classroom.id:
                violations.append({
                    "teacher": t,
                    "preference": p,
                    "preferred_classroom": preferred_classroom,
                })

    if not violations:
        return ConstraintError(name="matches_teacher_room_preference")

    max_weight = max(v["teacher"].weight for v in violations)
    penalty = weight * max_weight

    return ConstraintError(
        name="matches_teacher_room_preference",
        penalty=penalty,
        message="Занятие не соответствует предпочтению преподавателя по аудитории",
        data={
            "violations": violations,
        }
    )

@constraint("matches_teacher_time_preference")
def matches_teacher_time_preference(lesson: Lesson, *, weight) -> ConstraintError:

    teachers = list(lesson.teachers.all())
    slot = lesson.timeslot

    if slot is None:
        return ConstraintError(name="matches_teacher_time_preference")

    # Список нарушений (собираем для нескольких преподавателей)
    violations = []

    for t in teachers:
        excluded = ExcludedTimeslot.objects.filter(
            teacher=t,
            timeslot=slot,
            status=RequestStatus.VERIFIED  # только одобренные заявки
        )

        if excluded.exists():
            violations.append({
                "teacher": t,
                "excluded": list(excluded),  # модели заявок
                "timeslot": slot,            # модель timeslot
            })

    if not violations:
        return ConstraintError(name="matches_teacher_time_preference")

    # Максимальный вес преподавателя в конфликте
    max_teacher_weight = max(v["teacher"].weight for v in violations)
    penalty = weight * max_teacher_weight

    return ConstraintError(
        name="matches_teacher_time_preference",
        penalty=penalty,
        message="Занятие назначено  для преподавателя ",
        data={
            "violations": violations
        }
    )

@constraint("building_change")
def building_change(lesson: Lesson, *, weight) -> ConstraintError:

    # проверяем, стоит ли занятие в сетке
    current_slot = lesson.timeslot
    if not lesson.timeslot:
        return ConstraintError(name="building_change")
    

    # classroom = lesson.classroom
    # from_building = classroom.building if classroom else None

    teacher_ids = lesson.teachers.values_list("id", flat=True)
    groups_ids = lesson.study_groups.values_list("id", flat=True)

    violations = []

    # Ищем следующее и предыдущее занятие у групп и преподавателей
    prev_lessons = (Lesson.objects
                    .filter(scenario__id=lesson.scenario.id) # отбор по варианту расписания
                    .filter( # отбор по времени пары
                        timeslot__day=lesson.timeslot.day,
                        timeslot__order_number=lesson.timeslot.order_number - 1)
                    .filter( # отбор по группам и преподавателям
                        Q(teachers__id__in=teacher_ids) |
                        Q(study_groups__id__in=groups_ids))
                    .distinct())

    next_lessons = (Lesson.objects
                    .filter(scenario__id=lesson.scenario.id)
                    .filter(
                        timeslot__day=lesson.timeslot.day,
                        timeslot__order_number=lesson.timeslot.order_number + 1)
                    .filter(
                        Q(teachers__id__in=teacher_ids) |
                        Q(study_groups__id__in=groups_ids))
                    .distinct())

    # Функция проверки перехода между двумя аудиториями
    def check_transition(source: Lesson, destination: Lesson):
        src_room = source.classroom
        dst_room = destination.classroom
        if not src_room or not dst_room:
            return 9999  # невозможный переход

        b1 = src_room.building.id
        b2 = dst_room.building.id

        if b1 == b2:
            return 0

        travel = BuildingTravelTime.objects.filter(
            from_building__id=b1,
            to_building__id=b2
        ).first()

        return travel.travel_time_minutes if travel else 9999

    # Проверка левой границы (предыдущий → текущий)
    for prev in prev_lessons:
        travel = check_transition(prev, lesson)
        available = (
            current_slot.time_start.hour * 60 + current_slot.time_start.minute
            - (prev.timeslot.time_end.hour * 60 + prev.timeslot.time_end.minute)
        )

        if travel > available:
            violations.append({
                "from_lesson": prev,
                "to_lesson": lesson,
                "travel_minutes": travel,
                "available_minutes": available 
            })

    # Проверка правой границы (текущий → следующий)
    for nxt in next_lessons:
        travel = check_transition(lesson, nxt)
        available = (
            nxt.timeslot.time_start.hour * 60 + nxt.timeslot.time_start.minute
            - (current_slot.time_end.hour * 60 + current_slot.time_end.minute)
        )

        if travel > available:
            violations.append({
                "from_lesson": lesson,
                "to_lesson": nxt,
                "travel_minutes": travel,
                "available_minutes": available
            })

    if not violations:
        return ConstraintError(name="building_change")

    # Находим максимальный вес участника

    return ConstraintError(
        name="building_change",
        penalty=weight,
        message="Недостаточно времени для перехода между корпусами",
        data={
            "lesson": lesson,
            "violations": violations,
        }
    )

@constraint("students_gap")
def students_gap(lesson: Lesson, *, weight) -> ConstraintError:
    slot = lesson.timeslot
    if not slot:
        return ConstraintError(name="students_gap")
    groups_ids = lesson.study_groups.values_list("id", flat=True)

    violations = []

    for g in groups_ids:
        prev = (Lesson.objects
                .filter(scenario__id=lesson.scenario.id)
                .filter(study_groups__id=g.id)
                .filter(
                    timeslot__day=slot.day,
                    timeslot__order_number__lt=slot.order_number
                    )
                .order_by("-timeslot__order_number")
                .first()
                )
        next = (Lesson.objects
                .filter(scenario__id=lesson.scenario.id)
                .filter(study_groups__id=g.id)
                .filter(
                    timeslot__day=slot.day,
                    timeslot__order_number__gt=slot.order_number
                    )
                .order_by("-timeslot__order_number")
                .first()
                )
        
        if prev and prev.timeslot.order_number != slot.order_number - 1:
            violations.append({
                "order": prev.timeslot.order_number,
                "group": g,
                "lesson": prev
            })
        if next and next.timeslot.order_number != slot.order_number - 1:
            violations.append({
                "order": next.timeslot.order_number,
                "group": g,
                "lesson": next
            })

    if not violations:
        return ConstraintError(name="students_gap") 
    return ConstraintError(
        name="students_gap",
        penalty=weight,
        message="У некоторых групп возникает окно",
        data=violations
    )

@constraint("teachers_gap")
def teachers_gap(lesson: Lesson, *, weight) -> ConstraintError:
    slot = lesson.timeslot
    if not slot:
        return ConstraintError(name="teachers_gap")
    teachers_ids = lesson.teachers.values_list("id", flat=True)

    violations = []

    for t in teachers_ids:
        prev = (Lesson.objects
                .filter(scenario__id=lesson.scenario.id)
                .filter(teachers__id=t.id)
                .filter(
                    timeslot__day=slot.day,
                    timeslot__order_number__lt=slot.order_number
                    )
                .order_by("-timeslot__order_number")
                .first()
                )
        next = (Lesson.objects
                .filter(scenario__id=lesson.scenario.id)
                .filter(teachers__id=t.id)
                .filter(
                    timeslot__day=slot.day,
                    timeslot__order_number__gt=slot.order_number
                    )
                .order_by("-timeslot__order_number")
                .first()
                )
        
        if prev and prev.timeslot.order_number != slot.order_number - 1:
            violations.append({
                "order": prev.timeslot.order_number,
                "teacher": t,
                "lesson": prev
            })
        if next and next.timeslot.order_number != slot.order_number - 1:
            violations.append({
                "order": next.timeslot.order_number,
                "teacher": t,
                "lesson": next
            })

    if not violations:
        return ConstraintError(name="teachers_gap") 
    return ConstraintError(
        name="teachers_gap",
        penalty=weight,
        message="У некоторых преподавателей возникает окно",
        data=violations
    )

@constraint("teacher_overload")
def teacher_overload(lesson: Lesson, *, weight) -> ConstraintErro:
    slot = lesson.timeslot
    if not slot:
        return ConstraintError(name="teachers_gap")
    teachers_ids = lesson.teachers.values_list("id", flat=True)

    violations = []

    for t in teachers_ids:
        lesson_count = (Lesson.objects
                .filter(scenario__id=lesson.scenario.id)
                .filter(teachers__id=t.id)
                .filter(timeslot__week_num=slot.week_num)
                .count()
                )
        if lesson_count > os.getenv("MAX_ACADEMIC_LOAD",17):
            violations.append({
                "teacher":t,
                "current_load":lesson_count
            })
    if not violations:
        return ConstraintError(name="teacher_overload") 
    return ConstraintError(
        name="teacher_overload",
        penalty=weight,
        message="У некоторых преподавателей превышена нагрузка",
        data=violations
    )