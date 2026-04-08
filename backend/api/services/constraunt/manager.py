import logging
from typing import List

from api.models import Constraint, Lesson
from api.services.constraunt.constraints import registry
from api.services.constraunt.meta import ConstraintError
from api.services.schedule.draft.context import draft_context


logger = logging.getLogger("constraints")

class ConstraintManager:
    """Класс для управления проверкой ограничений"""
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
        return self

    def check_lesson(self, lesson):
        errors = []
        for c in self.constraints:
            func = self.methods.get(c.name)
            if func is None:
                continue
            result = func(lesson, weight=c.weight)
            if result:
                errors.append(result)
        return errors

    def check_scenario(self, scenario_id):
        errors = []
        for lesson in Lesson.objects.filter(scenario_id = scenario_id):
            errors.extend(self.check_lesson(lesson))
        return errors

    def check_lesson_draft(self, scenario_id, lesson_id, storage):
        """
        Проверяет Lesson в черновом контексте.
        """
        with draft_context(scenario_id, storage):
            lesson = Lesson.objects.get(id=lesson_id)
            return self.check_lesson(lesson)

    def check_scenario_draft(self, scenario_id, storage):
        """
        Проверяет весь сценарий в черновом контексте.
        """
        with draft_context(scenario_id, storage):
            return self.check_scenario(scenario_id)

    def prepare_draft_lesson(self, scenario_id, lesson_id, data, storage):
        """
        Сохраняет изменения занятия в Redis, подмешивает и проверяет.
        """
        # Записываем diff
        storage.update_lesson(lesson_id, data)

        # Проверка
        errors = self.check_lesson_draft(scenario_id, lesson_id, storage)

        return errors