import json
import uuid
from typing import Any, Dict, Optional, List

from django.core.cache import cache


class RedisDraftStorage:
    """
    Хранилище черновых изменений расписания:
    - изменения существующих Lesson по ID
    - новые Lesson без ID (ключ new:<uuid>)
    - удалённые Lesson (список в поле 'removed')
    """

    def __init__(self, scenario_id: int, user_id: str):
        self.scenario_id = scenario_id
        self.session_id = user_id
        self.key = f"schedule:{scenario_id}:user:{user_id}"

    # --- ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ---

    def _hgetall(self) -> Dict[str, Any]:
        raw = cache.hgetall(self.key)
        result = {}
        for k, v in raw.items():
            try:
                result[k] = json.loads(v)
            except Exception:
                result[k] = v
        return result

    def _hset(self, field: str, value: Any):
        cache.hset(self.key, field, json.dumps(value))

    def _hdel(self, field: str):
        cache.hdel(self.key, field)

    # --- ОСНОВНЫЕ ОПЕРАЦИИ ---

    def list_changes(self) -> Dict[str, Any]:
        """Возвращает весь хэш (включая new и removed)."""
        return self._hgetall()

    def get_lesson(self, lesson_key: str) -> Optional[Dict[str, Any]]:
        """Возвращает diff занятия по ключу (id или new:uuid)."""
        value = cache.hget(self.key, lesson_key)
        return json.loads(value) if value else None

    def set_lesson(self, lesson_id: int, data: Dict[str, Any]):
        """Сохраняет изменения для существующего занятия."""
        self._hset(str(lesson_id), data)

    def delete_lesson_diff(self, lesson_id: int):
        """Удаляет diff существующего занятия."""
        self._hdel(str(lesson_id))

    # --- НОВЫЕ ЗАНЯТИЯ ---

    def add_new_lesson(self, data: Dict[str, Any]) -> str:
        """
        Добавляет новое занятие (без id).
        Возвращает ключ new:<uuid>.
        """
        key = f"new:{uuid.uuid4()}"
        self._hset(key, data)
        return key

    def delete_new_lesson(self, new_key: str):
        """Удаляет новое занятие."""
        if new_key.startswith("new:"):
            self._hdel(new_key)

    # --- УДАЛЕНИЕ ЗАНЯТИЙ (МИГРАЦИЯ ИЛИ СНЯТИЕ) ---

    def mark_removed(self, lesson_id: int):
        """
        Помечает занятие как удалённое.
        Это soft-delete для черновика.
        """
        removed = self.get_removed()
        if lesson_id not in removed:
            removed.append(lesson_id)
            self.set_removed(removed)

    def unmark_removed(self, lesson_id: int):
        """Убирает занятие из списка удалённых."""
        removed = self.get_removed()
        if lesson_id in removed:
            removed.remove(lesson_id)
            self.set_removed(removed)

    def get_removed(self) -> List[int]:
        """Возвращает список удалённых занятий."""
        data = self.get_lesson("removed")
        return data if isinstance(data, list) else []

    def set_removed(self, ids: List[int]):
        """Записывает новый список удалённых занятий."""
        self._hset("removed", ids)

    # --- ОЧИСТКА ---

    def clear(self):
        """Полностью очищает черновики по сессии."""
        cache.delete(self.key)
