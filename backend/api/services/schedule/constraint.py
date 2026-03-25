from dataclasses import dataclass
import logging
from turtle import reset
from typing import Any, List

from api.models.models import Constraint, Lesson

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
#     ("Пересечение по аудиториям", 500, "no_room_overlap"),
#     ("Аудитория вмещает всех студентов", 500, "room_has_enough_seats"),
#     ("Аудитория соответствует оборудованию", 400, "room_meets_equipment_requirements"),
#     ("Предпочтения преподавателя по аудитории", 300, "matches_teacher_room_preference"),
#     ("Предпочтения преподавателя по времени", 200, "matches_teacher_time_preference"),
#     ("Переход между корпусами", 500, "building_change"),
#     ("Окно у студентов", 100, "students_gap"),
#     ("Окно у преподавателя", 50, "teacher_gap"), # Тоже важно, оказывается, но парвда окно у препода побольше
#     ("Перегрузка преподователя",50,"teacher_overload")
# ]
@dataclass
class ConstraintError ():
    name: str
    penalty: int = 0
    message: str = "OK"
    data: dict = {} # ПО идее сюда можно запихнуть что угодно, например занятия, с которыми возникает ошибка

class ConstraintManager():
    '''Сессия проверки расписания Проверяет ограничения из бд и проверяет есть ли его реализация'''
   
    def __init__(self):
        self.constraints = []
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
                    # добавляем имя для отчётности
                    result["name"] = c.name
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
        .filter(timeslot=slot)
        .filter(teachers__id__in=teacher_ids)
        .exclude(id=lesson.id) # type: ignore
        .distinct()
    )

    # нет конфликтов → возвращаем "пустую" ошибку
    if not conflicts.exists():
        return ConstraintError(name="teacher_no_overlap")

    conflict_entries = []
    penalties = []

    for conf in conflicts:
        common_teachers = list(conf.teachers.filter(id__in=teacher_ids))
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