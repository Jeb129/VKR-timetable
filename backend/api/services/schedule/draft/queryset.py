from typing import Iterable, List
from django.db.models import QuerySet
from api.models.schedule import Lesson

from api.services.redis.storage import RedisDraftStorage


class DraftLessonQuerySet:
    """
    Обёртка над QuerySet Lesson, которая накладывает черновые изменения
    поверх результатов запроса.
    """

    def __init__(self, base_qs: QuerySet, redis_storage: RedisDraftStorage):
        self.base_qs = base_qs
        self.redis = redis_storage

    # Проксирование методов QuerySet
    def __getattr__(self, item):
        """
        Проксируем методы QuerySet: filter, exclude, select_related и т.д.
        """

        def wrapper(*args, **kwargs):
            new_qs = getattr(self.base_qs, item)(*args, **kwargs)
            return DraftLessonQuerySet(new_qs, self.redis)

        return wrapper

    # Материализация набора объектов
    def apply_drafts(self, lessons: Iterable[Lesson]) -> List[Lesson]:
        drafts = self.redis.list_changes()

        removed = drafts.get("removed", [])
        result = []

        # --- Обрабатываем существующие объекты ---
        for les in lessons:
            if les.id in removed:
                continue

            diff = drafts.get(str(les.id))
            if diff:
                # Применяем изменение timeslot
                if "timeslot" in diff:
                    les.timeslot_id = diff["timeslot"]

                # Применяем изменение classroom
                if "classroom" in diff:
                    les.classroom_id = diff["classroom"]

            result.append(les)

        # --- Добавляем новые занятия ---
        for key, data in drafts.items():
            if not key.startswith("new:"):
                continue

            new_lesson = Lesson(
                id=None,
                scenario=self.base_qs.model().scenario,  # будет заменено при DraftScenario
                discipline_id=data["discipline"],
                lesson_type_id=data["lesson_type"],
                timeslot_id=data.get("timeslot"),
                classroom_id=data.get("classroom"),
            )

            # M2M для новых занятий пока откладываем (будет второй шаг)
            result.append(new_lesson)

        return result

    # Основные методы материализации
    def __iter__(self):
        return iter(self._apply_drafts(list(self.base_qs)))

    def all(self):
        """Сохраняем chainability."""
        return DraftLessonQuerySet(self.base_qs.all(), self.redis)

    def get(self, *args, **kwargs):
        obj = self.base_qs.get(*args, **kwargs)
        result = self._apply_drafts([obj])
        return result[0]

    def first(self):
        obj = self.base_qs.first()
        if obj is None:
            return None
        return self._apply_drafts([obj])[0]

    def last(self):
        obj = self.base_qs.last()
        if obj is None:
            return None
        return self._apply_drafts([obj])[0]

    def count(self):
        """count() должен учитывать новые и удалённые записи."""
        drafts = self.redis.list_changes()
        removed = drafts.get("removed", [])
        base_count = self.base_qs.count()
        new_count = len([1 for k in drafts if k.startswith("new:")])
        return base_count - len(removed) + new_count
