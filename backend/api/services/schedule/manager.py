import logging
from typing import List

from api.models import Constraint, Lesson
from api.services.constraunt.constraints import registry
from api.services.constraunt.context import ScheduleContext
from api.services.constraunt.meta import ConstraintError
from api.services.drafts.storage import ScheduleDraftStorage
from api.services.drafts.commit import commit_lesson, commit_scenario
from api.services.drafts.context import draft_context
from authentification.models import CustomUser

logger = logging.getLogger("constraints")

class ScheduleManager:
    """Класс, управляющий расписанием и проверками"""

    def _check_lesson_scenario(self,*,lesson_id=None,lesson=None):
        """Проверяет, что редактируемое занятие принадлежит текущему  сценарию"""
        if lesson is None and lesson_id is None:
            raise ValueError("не передана информация о занятии")
        if lesson is None:
            lesson = Lesson._default_manager.get(id=lesson_id)
        if lesson.scenario_id != self.scenario_id:
            raise ValueError("Занятие не является частью текущего сценария")

    
    def __init__(self,scenario_id: int,user: CustomUser):
        self.constraints: List[Constraint] = []
        self.methods = {}
        
        self.context = None

        self.scenario_id=scenario_id
        self.user=user
        self.storage = ScheduleDraftStorage(scenario_id=scenario_id,user_id=user.id)

    def build_context(self):
        self.context = ScheduleContext.build(self.scenario_id)
        return self

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
    

    def check_lesson(self, lesson, constraint_name = None):
        """Проверяет занятие в сценарии по всем ограничениям"""
        if self.context is None:
            raise ValueError("не выполнена загрузка контекста занятий для проверки")

        self._check_lesson_scenario(lesson=lesson)

        errors = []
        if constraint_name:
            constraints = [c for c in self.constraints if c.name == constraint_name]
        else:
            constraints = self.constraints
        for c in constraints:
            func = self.methods.get(c.name)
            if func is None:
                continue
            try:
                logger.debug("Проверка ограничения %s", c.name)
                errors.append(func(lesson, self.context, weight=c.weight))
            except Exception as err:
                logger.error("Ошибка при проверке ограничения %s для занятия %s", c.name, lesson.id)
                # logger.debug(err.with_traceback())
                errors.append(ConstraintError(
                    name=c.name,
                    message="Ошибка при проверке",
                    data=err
                ))
        return errors


    def check_scenario(self):
        """Проверяет все занятия в сценарии"""
        self.build_context()
        errors = []
        for lesson in self.context.lessons:
            errors.extend(self.check_lesson(lesson))
        return errors

    def check_lesson_draft(self, lesson_id):
        """Проверяет занятия в черновом контексте."""
        with draft_context(self.scenario_id, self.storage):
            self.build_context()
            lesson = Lesson.objects.get(id=lesson_id)
            return self.check_lesson(lesson)

    def check_scenario_draft(self):
        """Проверяет весь сценарий в черновом контексте."""
        with draft_context(self.scenario_id, self.storage):
            return self.check_scenario(self.scenario_id)


    def get_lessons_draft(self,*args,**kwargs):
        with draft_context(self.scenario_id, self.storage):
            return Lesson.objects.filter(*args,**kwargs)

    def update_lesson_draft(self,lesson_id, diff_data):
        """Вносит изменения в черновик расписания"""
        self._check_lesson_scenario(lesson_id=lesson_id)
        if diff_data:
            self.storage.update_lesson(lesson_id=lesson_id,diff=diff_data)
        return self.check_lesson_draft(lesson_id)
    
    def delete_lessons_draft(self, lesson_id=None):
        self._check_lesson_scenario(lesson_id=lesson_id)
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
