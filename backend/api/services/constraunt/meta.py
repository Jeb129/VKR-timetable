from dataclasses import dataclass
import logging
from typing import Any

logger = logging.getLogger("constraints")

registry = {}
hard_constraints = {}
soft_constraints = {}



def constraint(name, isHard = False):
    """Регистрирует функцию проверки под именем ограничения."""
    # logger.debug("Регистрация метода %s", name)

    def decorator(func):
        if name not in registry:
            registry[name] = func
            if isHard:
                hard_constraints[name] = func
            else:
                soft_constraints[name] = func
        return func
    return decorator

@dataclass
class ConstraintError ():
    name: str
    penalty: int = 0
    message: str = "OK"
    data: Any = None # По идее сюда можно запихнуть что угодно, например занятия, с которыми возникает ошибка
