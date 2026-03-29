from dataclasses import dataclass
from typing import Any


registry = {}
def constraint(name):
    """Регистрирует функцию проверки под именем ограничения."""
    def decorator(func):
        registry[name] = func
        return func
    return decorator

@dataclass
class ConstraintError ():
    name: str
    penalty: int = 0
    message: str = "OK"
    data: Any = None # По идее сюда можно запихнуть что угодно, например занятия, с которыми возникает ошибка
