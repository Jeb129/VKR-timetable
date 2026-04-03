from typing import Any
from django.db.models.manager import BaseManager

from api.services.schedule.draft.queryset import DraftLessonQuerySet
from api.services.redis.storage import RedisDraftStorage


class DraftLessonManager(BaseManager):
    """
    Оборачивает обычный RelatedManager (scenario.lessons)
    и заменяет его методы на работу через DraftLessonQuerySet.
    """

    def __init__(self, related_manager, redis_storage: RedisDraftStorage):
        super().__init__()
        self.related_manager = related_manager
        self.redis = redis_storage

    # Основные методы
    def all(self):
        qs = self.related_manager.all()
        return DraftLessonQuerySet(qs, self.redis)

    def filter(self, *args, **kwargs):
        qs = self.related_manager.filter(*args, **kwargs)
        return DraftLessonQuerySet(qs, self.redis)

    def exclude(self, *args, **kwargs):
        qs = self.related_manager.exclude(*args, **kwargs)
        return DraftLessonQuerySet(qs, self.redis)

    def get(self, *args, **kwargs):
        """
        get() должен вернуть урок с применёнными черновыми изменениями.
        """
        qs = self.related_manager.all()
        draft_qs = DraftLessonQuerySet(qs, self.redis)
        obj = qs.get(*args, **kwargs)
        return draft_qs.apply_drafts([obj])[0]

    def count(self) -> int:
        """count() должен учитывать новые и удалённые занятия."""
        drafts = self.redis.list_changes()
        removed = drafts.get("removed", [])
        base_count = self.related_manager.count()
        new_count = len([1 for k in drafts if k.startswith("new:")])
        return base_count - len(removed) + new_count

    # Проксирование остальных методов RelatedManager
    def __getattr__(self, item: str) -> Any:
        """
        Для select_related, prefetch_related, order_by и других
        возвращаем DraftLessonQuerySet.
        """
        if hasattr(self.related_manager, item):

            def wrapper(*args, **kwargs):
                qs = getattr(self.related_manager, item)(*args, **kwargs)
                return DraftLessonQuerySet(qs, self.redis)

            return wrapper

        return super().__getattribute__(item)
