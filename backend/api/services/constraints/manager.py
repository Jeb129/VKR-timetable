from dataclasses import dataclass
from email.policy import default
import logging
from typing import Dict, List

from api.models import Lesson
from api.services.constraints.meta import ConstraintError, LessonError

import api.services.constraints.methods
from api.services.constraints.meta import registry

from api.models import Constraint
from api.services.schedule.context import ScheduleContext
logger = logging.getLogger("constraints")

class ConstraintManager:
    """
    Менеджер для методов проверки ограничений. 
    Подгружает информацию об ограничениях из БД и сопостовляет с методами
    """
    def __init__(self):
        self.constraints: Dict[str,Constraint] = {}
        self.methods: Dict[str, callable] = {}
        self._load_constraints()

    def _load_constraints(self):
        """Загружает ограничения и сопоставляет с реализованными функциями."""
        logger.info("Проверка реализации ограничений")

        for c in Constraint.objects.all():
            func = registry.get(c.name)
            if func:
                self.constraints[c.name] = c
                self.methods[c.name] = func
                logger.debug("Успешная инициализация ограничения %s", c.name)
            else:
                logger.warning("Метод проверки ограничения '%s' не найден.",c.name)

    def _select_constraints(
        self,
        *,
        name: str | None = None,
        level: int = 0,              # 0 = все, 1 = soft, 2 = hard
        manual_only: bool | None = None,
        generation_only: bool | None = None,
    ) -> Dict[str, callable]:
        """Выбирает ограничения по фильтрам из списка методов"""
        selected = {}

        for cname, constraint in self.constraints.items():
            func = self.methods[cname]

            # 1) Фильтр по имени
            if name is not None and cname != name:
                continue

            # 2) Фильтр по уровню
            if level == 1 and constraint.is_hard:      # soft-only
                continue
            if level == 2 and not constraint.is_hard:  # hard-only
                continue

            # 3) Фильтр по manual_only
            if generation_only and constraint.manual_only:
                continue
            if manual_only and constraint.generation_only:
                continue

            selected[cname] = func

        return selected

    def check(
        self,*,lesson: Lesson, context:ScheduleContext,
        constraint_name:str = None, 
        constraint_level: int = 0, 
        manual_only: bool=None,
        generation_only: bool=None,
    ) -> List[ConstraintError]:
        """
        Проверяет переданное занятие по всем ограничениям, относительно индексированных занятий в контексте

        Обязательные параметры
            :lesson: Проверяемое занятие
            :context: Индексированный список занятий

        Дополнительные параметры
            :constraint_name: Имя конкретного ограничения для проверки
            :generation_only: Проверка только по ограничениям для генератора
            :manual_only: Проверка только по ограничениям для ручных изменений
            :constraint_level: Используемый список для проверки
                - 0 (default) - Проверка по всем существующим ограничениям
                - 1 - Проверка по списку мягких ограничений
                - 2 - Проверка по списку жестких ограничений

        Возврат:
        List[ConstraintError] - список обнаруженных при проверке конфликтов
        """
        if lesson is None:
            raise ValueError("lesson is None")
        if context is None:
            raise ValueError("context is None")

        funcs = self._select_constraints(
            name=constraint_name,
            level=constraint_level,
            manual_only=manual_only,
            generation_only=generation_only,
        )

        errors: List[ConstraintError] = []
        for cname, func in funcs.items():
            constraint_obj = self.constraints[cname]
            # result = func(lesson=lesson, context=context, weight=constraint_obj.weight)
            # if result:
            #     errors.append(result)
            try:
                result = func(lesson=lesson, context=context, weight=constraint_obj.weight)
                if result:
                    errors.append(result)
            except Exception as err:
                errors.append(ConstraintError(
                    name=cname,
                    message="Ошибка при проверке",
                    data=str(err)
                ))
        return errors
