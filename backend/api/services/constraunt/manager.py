import logging
from typing import List

from api.models import Constraint, Lesson
from api.services.constraunt.constraints import registry
from api.services.constraunt.meta import ConstraintError


logger = logging.getLogger("constraints")

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
                logger.warning("Ограничение '%s' не реализовано.",c.name)
                continue

            self.constraints.append(c)
            self.methods[c.name] = func

    def check_lesson(self, lesson: Lesson) -> List[ConstraintError]:
        """Проверяет одно занятие всеми реализованными ограничениями."""
        errors: List[ConstraintError] = []

        for c in self.constraints:
            func = self.methods.get(c.name)
            if func is None:
                continue

            result = func(lesson, weight=c.weight)
            if result:
                errors.append(result)

        return errors

    def check_scenario(self, scenario) -> List[ConstraintError]:
        """Проверяет всё расписание."""
        errors: List[ConstraintError] = []
        for lesson in scenario.lessons.all():
            errors.extend(self.check_lesson(lesson))
        return errors
