import logging
from datetime import datetime
from typing import Dict
from django.core.cache import cache
from celery.result import AsyncResult

from api.tasks import run_generation_task
from celery.signals import task_postrun
from config.settings.celery import app as celery_app

logger = logging.getLogger("task_manager")

class GenerationTaskManager:
    """
    Менеджер для управления жизненным циклом Celery-задач генерации расписания.
    Обеспечивает контроль ресурсов, мониторинг статуса и механизмы остановки.
    """
    
    # Ключи для Redis
    META_KEY_PREFIX = "gen_meta:"
    COUNTER_KEY = "active_generations_count"
    
    # Настройки лимитов
    MAX_PARALLEL_TASKS = 2  # Максимальное число одновременных генераций
    TASK_TIMEOUT = 60 * 60 * 24  # Срок жизни метаданных в кеше (1 день)

    @classmethod
    def _get_meta_key(cls, scenario_id: int) -> str:
        return f"{cls.META_KEY_PREFIX}{scenario_id}"

    @classmethod
    def start_task(cls, scenario_id, semester_id, user_id, constraints_data, solver_params):
        meta_key = cls._get_meta_key(scenario_id)
        metadata = cache.get(meta_key)

        # ПРОВЕРКА НА ЗОМБИ-ЗАДАЧУ
        if metadata:
            task_id = metadata.get("task_id")
            res = AsyncResult(task_id)
            
            # Если задача в Celery уже закончена (SUCCESS, FAILURE, REVOKED)
            # или ее статус неизвестен, значит запись в Redis — мусор
            if res.state in ['SUCCESS', 'FAILURE', 'REVOKED'] or res.state is None:
                logger.warning(f"Обнаружена зомби-задача {task_id} для сценария {scenario_id}. Очистка...")
                cls.finalize_task(scenario_id)
            else:
                raise ValueError("Генерация для этого сценария уже выполняется.")

        # Атомарная проверка лимита
        if cache.get(cls.COUNTER_KEY) is None:
            cache.set(cls.COUNTER_KEY, 0, timeout=None)

        current_count = cache.get(cls.COUNTER_KEY, 0)
        if current_count >= cls.MAX_PARALLEL_TASKS:
            raise RuntimeError("Сервер перегружен. Подождите завершения других задач.")

        metadata = {
            "scenario_id": scenario_id,
            "semester_id": semester_id,
            "user_id": user_id,
            "start_time": datetime.now().isoformat(),
            "stop_signal": False
        }

        # Запуск задачи
        task = run_generation_task.delay(scenario_id, constraints_data, solver_params)
        metadata["task_id"] = task.id
        
        cache.set(meta_key, metadata, timeout=86400)
        cache.incr(cls.COUNTER_KEY)
        return task.id

    @classmethod
    def stop_task(cls, scenario_id: int) -> bool:
        """
        Подает сигнал к остановке через Redis и делает отзыв задачи в Celery.
        """
        meta_key = cls._get_meta_key(scenario_id)
        metadata = cache.get(meta_key)

        if not metadata:
            logger.warning(f"Попытка остановить несуществующую задачу для сценария {scenario_id}")
            return False

        # 1. Подаем "мягкий" сигнал для StopSentinel
        metadata["stop_signal"] = True
        cache.set(meta_key, metadata, timeout=cls.TASK_TIMEOUT)

        # 2. Посылаем Celery сигнал прерывания (SIGTERM)
        # Это сработает, если OR-Tools долго не находит новых решений
        celery_app.control.revoke(metadata["task_id"], terminate=True, signal='SIGTERM')
        
        logger.info(f"Подан сигнал остановки задаче {metadata['task_id']}")
        return True

    @classmethod
    def get_status(cls, scenario_id: int) -> Dict:
        """
        Возвращает сводную информацию о задаче из Кеша и Celery.
        """
        meta_key = cls._get_meta_key(scenario_id)
        metadata = cache.get(meta_key)

        if not metadata:
            return {"state": "IDLE"}

        # Добавляем актуальный статус из Celery
        res = AsyncResult(metadata["task_id"])
        metadata["celery_state"] = res.state  # PENDING, STARTED, SUCCESS, etc.
        
        return metadata

    @classmethod
    def finalize_task(cls, scenario_id: int):
        """
        Очищает метаданные и декрементирует счетчик.
        Метод ДОЛЖЕН вызываться в finally блоке Celery задачи.
        """
        meta_key = cls._get_meta_key(scenario_id)
        if cache.get(meta_key):
            cache.delete(meta_key)
            
            # Уменьшаем счетчик активных задач
            current = cache.get(cls.COUNTER_KEY)
            if current is not None and current > 0:
                cache.decr(cls.COUNTER_KEY)
            elif current is not None and current <= 0:
                # На всякий случай не уходим в минус
                cache.set(cls.COUNTER_KEY, 0, timeout=None)
            
            logger.info(f"Ресурсы для сценария {scenario_id} освобождены.")

    @task_postrun.connect(sender=run_generation_task)
    def on_generation_task_finished(sender, task_id, kwargs, **extra):
        """
        Срабатывает автоматически после завершения задачи run_generation_task.
        Выполняется ДАЖЕ если задача упала с ошибкой или была отозвана (revoke).
        """
        scenario_id = kwargs.get('scenario_id')
        if scenario_id:
            GenerationTaskManager.finalize_task(scenario_id)