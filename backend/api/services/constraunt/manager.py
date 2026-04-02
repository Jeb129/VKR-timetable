import logging
from typing import List

from api.models import Constraint, Lesson
from api.services.constraunt.constraints import registry
from api.services.constraunt.meta import ConstraintError,logger




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

class ConstraintManager():
    '''Сессия проверки расписания Проверяет ограничения из бд и проверяет есть ли его реализация'''
   
    def __init__(self):
        self.constraints: List[Constraint] = []
        self.methods = {}  
   
    def load(self):
        """Загружает ограничения и сопоставляет с реализованными функциями."""
        logger.debug("Проверка реализации ограничений ограничений")

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
 

