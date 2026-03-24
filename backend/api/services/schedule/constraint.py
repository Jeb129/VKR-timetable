import logging
from turtle import reset
from typing import Any, List

from api.models.models import Constraint

logger = logging.getLogger("constraints")


class ConstraintError ():
    penalty: int
    message: str
    data: Any # ПО идее сюда можно запихнуть что угодно, например занятия, с которыми возникает ошибка

class ConstraintSession():
    '''Сессия проверки расписания Проверяет ограничения из бд и проверяет есть ли его реализация'''
    constraints: List[Constraint] = []

    def __init__(self):
        logger.info("Инициализация проверки ограничений")
        with Constraint.objects.all() as constraints:
            for c in constraints:
                method = getattr(self, c.name, None)
                if not method:
                    logger.warning(f"Не реализован метод проверки ограничения {c.name}")
                else:
                    self.constraints.append(c)
    
    def check_constraints(self, lesson) -> List[ConstraintError]:
        res = []
        for c in self.constraints:
            method = getattr(self, c.name, None)
            if method:
                res.append(method(lesson))
        return res

