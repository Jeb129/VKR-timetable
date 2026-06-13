import logging
from celery import shared_task
from api.models import ScheduleScenario, Constraint, enums
from api.services.schedule.generator import ScheduleGenerator

logger = logging.getLogger("celery_tasks")

@shared_task(name="api.tasks.run_generation_task") # Явно задаем имя для сигналов
def run_generation_task(scenario_id: int, constraints_data: list, solver_params: dict):
    """
    Фоновая задача: только логика генерации.
    """
    try:
        # 1. Статус "В процессе"
        ScheduleScenario.objects.filter(id=scenario_id).update(
            status=enums.GenerationStatus.IN_PROGRESS
        )

        # 2. Подготовка ограничений
        overrides = [Constraint(**d) for d in constraints_data] if constraints_data else None

        # 3. Инициализация и решение
        generator = ScheduleGenerator(
            scenario_id=scenario_id, 
            constraints=overrides
        )

        success = generator.solve(
            time_limit=solver_params.get('time_limit', 300),
            num_workers=solver_params.get('num_workers', 4)
        )

        # 4. Сохранение результата
        if success:
            generator.commit()
            ScheduleScenario.objects.filter(id=scenario_id).update(
                status=enums.GenerationStatus.SUCESS
            )
        else:
            ScheduleScenario.objects.filter(id=scenario_id).update(
                status=enums.GenerationStatus.INFEASIBLE
            )

    except Exception as exc:
        logger.error(f"Ошибка генерации {scenario_id}: {exc}", exc_info=True)
        ScheduleScenario.objects.filter(id=scenario_id).update(
            status=enums.GenerationStatus.ERROR
        )
        raise exc # Пробрасываем для Celery