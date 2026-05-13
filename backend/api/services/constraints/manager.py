import logging
from typing import Dict, List

import api.services.constraints.methods
from api.services.constraints.meta import registry

from api.models import Constraint
logger = logging.getLogger("constraints")


class ConstraintManager:
    def __init__(self):
        self.constraints: List[Constraint] = []
        self.hard: Dict[str, callable] = {}
        self.soft: Dict[str, callable] = {}
        self.all: Dict[str, callable] = {}
        self._load_constraints()

    def _load_constraints(self):
        """Загружает ограничения и сопоставляет с реализованными функциями."""
        logger.info("Проверка реализации ограничений")

        for c in Constraint.objects.all():
            func = registry.get(c.name)
            if func:
                self.constraints.append(c)
                self.all[c.name] = func
                if c.is_hard:
                    self.hard[c.name] = func
                else:
                    self.soft[c.name] = func
                logger.debug("Успешная инициализация ограничения %s", c.name)
            else:
                logger.warning("Метод проверки ограничения '%s' не найден.",c.name)