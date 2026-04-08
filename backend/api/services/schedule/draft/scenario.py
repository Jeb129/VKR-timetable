from api.services.schedule.draft.manager import DraftLessonManager


class DraftScenario:
    """
    Обёртка над моделью ScheduleScenario,
    которая заменяет менеджер lessons на DraftLessonManager.
    """

    def __init__(self, scenario, redis_storage):
        self._scenario = scenario
        self._redis = redis_storage

    def __getattr__(self, item):
        """
        Проксируем все атрибуты сценария,
        кроме lessons — его переопределяем.
        """
        if item == "lessons":
            return DraftLessonManager(self._scenario.lessons, self._redis)
        return getattr(self._scenario, item)

    @property
    def scenario(self):
        return self._scenario
