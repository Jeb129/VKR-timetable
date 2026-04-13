import logging
from typing import List

from api.models import Constraint, Lesson
from api.services.constraunt.constraints import registry
from api.services.constraunt.meta import ConstraintError
from api.services.schedule.draft.context import draft_context


logger = logging.getLogger("constraints")

class ConstraintManager:
    """Класс для управления проверкой ограничений"""

    constraints: List[Constraint] = []
    methods = {}  

    @classmethod
    def load(cls):
        """Загружает ограничения и сопоставляет с реализованными функциями."""
        logger.info("Проверка реализации ограничений ограничений")

        for c in Constraint.objects.all():
            func = registry.get(c.name)
            if func is None:
                logger.warning("Метод проверки ограничения '%s' не найден.",c.name)
                continue

            cls.constraints.append(c)
            cls.methods[c.name] = func
            logger.debug("Успешная инициализация ограничения %s", c.name)
        return
    
    @classmethod
    def check_lesson(cls, lesson):
        errors = []
        for c in cls.constraints:
            func = cls.methods.get(c.name)
            if func is None:
                continue
            result = func(lesson, weight=c.weight)
            if result:
                errors.append(result)
        return errors
    
    @classmethod
    def check_scenario(cls, scenario_id):
        errors = []
        for lesson in Lesson.objects.filter(scenario_id = scenario_id):
            errors.extend(cls.check_lesson(lesson))
        return errors

    def check_lesson_draft(cls, scenario_id, lesson_id, storage):
        """
        Проверяет Lesson в черновом контексте.
        """
        with draft_context(scenario_id, storage):
            lesson = Lesson.objects.get(id=lesson_id)
            return cls.check_lesson(lesson)

    @classmethod
    def check_scenario_draft(cls, scenario_id, storage):
        """
        Проверяет весь сценарий в черновом контексте.
        """
        with draft_context(scenario_id, storage):
            return cls.check_scenario(scenario_id)

    @classmethod
    def prepare_draft_lesson(cls, scenario_id, lesson_id, data, storage):
        """
        Сохраняет изменения занятия в Redis, подмешивает и проверяет.
        """
        # Записываем diff
        storage.update_lesson(lesson_id, data)

        # Проверка
        errors = cls.check_lesson_draft(scenario_id, lesson_id, storage)

        return errors