from dataclasses import dataclass
import logging
from typing import Any, Dict, List, Optional
from ortools.sat.python import cp_model

from api.models import Lesson, Constraint
from api.services.schedule.context import ScheduleContext

logger = logging.getLogger("constraints")

registry = {}


def constraint(name):
    """Регистрирует функцию проверки под именем ограничения."""
    def decorator(cls):
        if name not in registry:
            registry[name] = cls
            cls.name = name
        return cls
    return decorator

@dataclass
class ConstraintError ():
    name: str
    penalty: int = 0
    message: str = "OK"
    data: Any = None # По идее сюда можно запихнуть что угодно, например занятия, с которыми возникает ошибка

@dataclass
class LessonError:
    lesson: Lesson
    errors: List[ConstraintError]

class BaseConstraint:
    """Базовый класс для всех ограничений расписания"""
    
    def __init__(self,obj:Constraint):
        # Техническое имя будет браться из имени класса или задаваться вручную
        self.config:Constraint = obj

    def check(self, lesson: Lesson, context: ScheduleContext) -> Optional[ConstraintError]:
        return None

    def apply_to_model(self, model: cp_model.CpModel, lesson_vars: Dict, context: ScheduleContext):
        """
        Оркестратор для OR-Tools. 
        """
        if not self.config.is_active:
            return
        if self.config.manual_only:
            return

        if self.config.is_hard:
            self._build_hard(model, lesson_vars, context)
        else:
            self._build_soft(model, lesson_vars, context)

    def _build_hard(self, model: cp_model.CpModel, lesson_vars: Dict, context: ScheduleContext):
        """Реализация жесткого правила в OR-Tools"""
        raise NotImplementedError

    def _build_soft(self, model: cp_model.CpModel, lesson_vars: Dict, 
                               context: ScheduleContext):
        """Реализация мягкого правила в OR-Tools (через минимизацию штрафа)"""
        raise NotImplementedError