import logging
from typing import Any, Dict, List

from api.models import Lesson

from api.services.constraints import methods
from api.services.constraints.meta import BaseConstraint, ConstraintError, registry

from api.models import Constraint
from api.services.schedule.context import ScheduleContext
logger = logging.getLogger("constraints")

class ConstraintManager:
    """
    Менеджер для методов проверки ограничений. 
    Подгружает информацию об ограничениях из БД и сопостовляет с методами
    """
    def __init__(self, constraints):
        self.constraints: List[Constraint] = constraints or list(Constraint.objects.filter(is_active = True))
        self.methods: Dict[str, callable] = {}
        self.instances: Dict[str, BaseConstraint] = {}
        self._load_constraints()

    def _load_constraints(self):
        """Загружает ограничения и сопоставляет с реализованными функциями."""
        logger.info("Проверка реализации ограничений")

        for config in self.constraints:
            # Ищем класс реализации в реестре по техническому имени
            constraint_class = registry.get(config.name)
            
            if not constraint_class:
                logger.warning("Класс для ограничения '%s' не найден в реестре.",config.name)
                continue

            is_hard_able = config.is_hard and constraint_class._build_soft != BaseConstraint._build_hard 
            is_soft_able = not config.is_hard and constraint_class._build_soft != BaseConstraint._build_soft
            is_manual_able = constraint_class.check != BaseConstraint.check


            if not config.manual_only and not (is_hard_able or is_soft_able):
                logger.error("Используемое для генерации ограничение '%s' отмечено как %s но метод %s.%s в классе  не реализован. Помечено как 'только для ручных проверок' (локально)",
                            config.name,
                            "жесткое" if config.is_hard else "мягкое",
                            constraint_class.__name__,
                            "_build_hard" if config.is_hard else "_build_soft"
                            )
                config.manual_only = True
            
            if not config.generation_only and not is_manual_able:
                logger.error("Метод '%s.check' не реализован. Ограничение '%s' помечено как 'только для генерации' (локально)",
                             constraint_class.__name__,
                             config.name
                             )
                config.generation_only = True

            if config.manual_only and config.generation_only:
                logger.warning("Ограничение '%s' одновременно помечено как 'только для генерации' и 'только для ручных проверок'", config.name)
                continue


            # Создаем экземпляр класса, передавая ему конфиг из БД
            instance = constraint_class(config)
            self.instances[config.name] = instance

            logger.debug(f"Ограничение '{config.name}' инициализировано.")
                

    def _select_instances(
        self,
        *,
        name: str | None = None,
        level: int = 0,              # 0 = все, 1 = soft, 2 = hard
        manual_only: bool | None = None,
        generation_only: bool | None = None,
    ) -> List[BaseConstraint]:
        """Выбирает ограничения по фильтрам из списка методов"""
        selected = []

        for instance in self.instances.values():
            config = instance.config # Объект Constraint из БД

            # 1) Фильтр по имени
            if name is not None and config.name != name:
                continue

            # 2) Фильтр по уровню (Hard/Soft)
            if level == 1 and config.is_hard:      # только мягкие
                continue
            if level == 2 and not config.is_hard:  # только жесткие
                continue

            # 3) Фильтры по типу использования (ручной/генератор)
            if generation_only and config.manual_only:
                continue
            if manual_only and config.generation_only:
                continue

            selected.append(instance)

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

        targets = self._select_instances(
            name=constraint_name,
            level=constraint_level,
            manual_only=manual_only,
            generation_only=generation_only,
        )

        errors: List[ConstraintError] = []
        for instance in targets:
            try:
                # Вызываем обертку run_check (которая проверяет is_active внутри)
                result = instance.check(lesson, context)
                if result:
                    errors.append(result)
            except Exception as err:
                logger.error(f"Ошибка в ограничении {instance.config.name}: {err}", exc_info=True)
                errors.append(ConstraintError(
                    name=instance.config.name,
                    message="Внутренняя ошибка метода проверки",
                    data=str(err)
                ))
        return errors
    

    def apply_to_solver(
        self, 
        model: Any, 
        lesson_vars: Dict[int, Any], 
        context: ScheduleContext
    ):
        """
        Новый метод: Применяет все активные ограничения к модели OR-Tools.
        Используется только в генераторе.
        """
        # Для солвера выбираем все, что не помечено как manual_only
        solver_constraints = self._select_instances(generation_only=True)
        
        logger.info(f"Применение {len(solver_constraints)} ограничений к модели OR-Tools...")
        for instance in solver_constraints:
            try:
                instance.apply_to_model(model, lesson_vars, context)
            except NotImplementedError:
                logger.error(f"Ограничение '{instance.config.name}' не реализует метод для генерации!")
            except Exception as err:
                logger.error(f"Критическая ошибка при сборке модели в '{instance.config.name}': {err}")
                raise err
