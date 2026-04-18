import logging
from typing import List

from api.models import Constraint, Lesson
from api.services.constraunt.constraints import registry
from api.services.constraunt.meta import ConstraintError
from api.services.redis.storage import RedisDraftStorage
from api.services.schedule.draft.commit import commit_lesson, commit_scenario
from api.services.schedule.draft.context import draft_context
from authentification.models import CustomUser

logger = logging.getLogger("constraints")

class ScheduleManager:
    """Класс, управляющий расписанием и проверками"""

    def check_lesson_scenario(func):
        """Проверяет, что редактируемое занятие принадлежит текущему  сценарию"""
        def decorator(self,lesson_id,*args,**kwargs):
            lesson = Lesson._default_manager.get(id=lesson_id)
            if lesson.scenario_id != self.scenario_id:
                raise ValueError("Занятие не является частью текущего сценария")
            return func(self,lesson_id,*args,**kwargs)
        return decorator


    
    def __init__(self,scenario_id: int,user: CustomUser):
        self.constraints: List[Constraint] = []
        self.methods = {}

        self.scenario_id=scenario_id
        self.user=user
        self.storage = RedisDraftStorage(scenario_id=scenario_id,user_id=user.id)


    def init_constraints(self):
        """Загружает ограничения и сопоставляет с реализованными функциями."""
        logger.info("Проверка реализации ограничений")

        for c in Constraint.objects.all():
            func = registry.get(c.name)
            if func is None:
                logger.warning("Метод проверки ограничения '%s' не найден.",c.name)
                continue

            self.constraints.append(c)
            self.methods[c.name] = func
            logger.debug("Успешная инициализация ограничения %s", c.name)
        return self
    
    def check_lesson(self, lesson):
        """Проверяет занятие в сценарии по всем ограничениям"""
        errors = []
        for c in self.constraints:
            func = self.methods.get(c.name)
            if func is None:
                continue
            try:
                logger.debug("Проверка ограничения %s", c.name)
                errors.append(func(lesson, weight=c.weight))
            except Exception as err:
                logger.error("Ошибка при проверке ограничения для занятия %s",lesson.id)
                logger.debug(err.with_traceback())
                errors.append(ConstraintError(
                    name=c.name,
                    message="Ошибка при проверке",
                    data=err
                ))
        return errors


    def check_scenario(self):
        """Проверяет все занятия в сценарии"""
        errors = []
        for lesson in Lesson.objects.filter(scenario_id = self.scenario_id):
            errors.extend(self.check_lesson(lesson))
        return errors

    def check_lesson_draft(self, lesson_id):
        """Проверяет занятия в черновом контексте."""
        with draft_context(self.scenario_id, self.storage):
            lesson = Lesson.objects.get(id=lesson_id)
            return self.check_lesson(lesson)

    def check_scenario_draft(self):
        """Проверяет весь сценарий в черновом контексте."""
        with draft_context(self.scenario_id, self.storage):
            return self.check_scenario(self.scenario_id)

    @check_lesson_scenario
    def get_lessons_draft(self,**kwargs):
        with draft_context(self.scenario_id, self.storage):
            return Lesson.objects.filter(kwargs)

    @check_lesson_scenario
    def update_lesson_draft(self,lesson_id, diff_data):
        """Вносит изменения в черновик расписания"""
        if diff_data:
            self.storage.update_lesson(lesson_id=lesson_id,diff=diff_data)
        return self.check_lesson_draft(self.scenario_id, lesson_id, self.storage)
    
    @check_lesson_scenario
    def delete_lessons_draft(self, lesson_id=None):
        if lesson_id is not None:
            self.storage.delete_lesson(lesson_id=lesson_id)
        else:
            self.storage.clear_all()
    
    def create_lesson_draft(self,data):
        return self.storage.create_lesson(data=data)

    
    def apply_lessons(self, lesson_id=None):
        if lesson_id is None:
            commit_scenario(self.storage)
        else:
            commit_lesson(self.storage,lesson_id)
        

    def has_draft(self):
        return self.storage.has_any_changes()



class ScheduleManager_old:
    """Класс для управления проверкой ограничений"""

    def __init__(self):
        self.constraints: List[Constraint] = []
        self.methods = {}

    def load(self):
        """Загружает ограничения и сопоставляет с реализованными функциями."""
        logger.info("Проверка реализации ограничений")

        for c in Constraint.objects.all():
            func = registry.get(c.name)
            if func is None:
                logger.warning("Метод проверки ограничения '%s' не найден.",c.name)
                continue

            self.constraints.append(c)
            self.methods[c.name] = func
            logger.debug("Успешная инициализация ограничения %s", c.name)
        return self
    
    def check_lesson(self, lesson):
        """Проверяет занятие в сценарии по всем ограничениям"""
        errors = []
        for c in self.constraints:
            func = self.methods.get(c.name)
            if func is None:
                continue
            try:
                logger.debug("Проверка ограничения %s", c.name)
                errors.append(func(lesson, weight=c.weight))
            except Exception as err:
                logger.error("Ошибка при проверке ограничения для занятия %s",lesson.id)
                logger.debug(err.with_traceback())
                errors.append(ConstraintError(
                    name=c.name,
                    message="Ошибка при проверке",
                    data=err
                ))
        return errors
    
    def check_scenario(self, scenario_id):
        """Проверяет все занятия в сценарии"""
        errors = []
        for lesson in Lesson.objects.filter(scenario_id = scenario_id):
            errors.extend(self.check_lesson(lesson))
        return errors

    def check_lesson_draft(self, scenario_id, lesson_id, storage):
        """Проверяет занятия в черновом контексте."""
        with draft_context(scenario_id, storage):
            lesson = Lesson.objects.get(id=lesson_id)
            return self.check_lesson(lesson)

    def check_scenario_draft(self, scenario_id, storage):
        """Проверяет весь сценарий в черновом контексте."""
        with draft_context(scenario_id, storage):
            return self.check_scenario(scenario_id)

    def update_lesson_draft(self, scenario_id, lesson_id, data, storage):
        """Сохраняет изменения занятия в Redis, подмешивает и проверяет."""
        # Записываем diff
        if data:
            storage.update_lesson(lesson_id, data)

        # Проверка
        errors = self.check_lesson_draft(scenario_id, lesson_id, storage)

        return errors