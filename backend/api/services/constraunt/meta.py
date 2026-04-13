from dataclasses import dataclass
import logging
import re
from typing import Any

logger = logging.getLogger("constraints")

registry = {}



def constraint(name):
    """Регистрирует функцию проверки под именем ограничения."""
    # logger.debug("Регистрация метода %s", name)

    def decorator(func):
        def wrapper(*args,**kwargs):
            logger.debug("Проверка ограничения %s", name)
            return func(*args,**kwargs)

        if name not in registry:
            logger.debug("Регистрация метода %s", name)
            registry[name] = wrapper

        return wrapper
    return decorator

@dataclass
class ConstraintError ():
    name: str
    penalty: int = 0
    message: str = "OK"
    data: Any = None # По идее сюда можно запихнуть что угодно, например занятия, с которыми возникает ошибка
