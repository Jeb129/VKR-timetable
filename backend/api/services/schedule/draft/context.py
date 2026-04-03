from contextlib import contextmanager
from typing import Generator

from api.models.schedule import Lesson, ScheduleScenario
from api.services.schedule.draft.manager import DraftLessonManager
from api.services.schedule.draft.scenario import DraftScenario
from api.services.redis.storage import RedisDraftStorage


@contextmanager
def draft_context(
    scenario: ScheduleScenario, redis_storage: RedisDraftStorage
) -> Generator[DraftScenario, None, None]:
    """
    Контекст подменяет Lesson.objects на DraftLessonManager.
    Это необходимо, чтобы constraint-функции, которые выполняют
    Lesson.objects.filter(...), работали с черновиками.
    """

    # 1. Сохраняем оригинальный менеджер
    original_manager = Lesson.objects

    try:
        # 2. Подменяем Lesson.objects на наш DraftLessonManager
        Lesson.objects = DraftLessonManager(Lesson.objects, redis_storage)

        # 3. Возвращаем DraftScenario
        yield DraftScenario(scenario, redis_storage)

    finally:
        # 4. Восстанавливаем оригинальный менеджер
        Lesson.objects = original_manager
