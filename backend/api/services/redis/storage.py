import json
from typing import Dict, Any, List, Optional
from django_redis import get_redis_connection


class RedisDraftStorage:
    """
    Хранилище черновиков расписания в Redis.

    Структура ключа:
        schedule:{scenario_id}:user:{user_id}

    Структура данных в Redis (hash):
        updated -> JSON object {lesson_id: diff}
        created -> JSON object {new_uuid: diff}
        deleted -> JSON array [lesson_ids]
    """

    FIELD_UPDATED = "updated"
    FIELD_CREATED = "created"
    FIELD_DELETED = "deleted"

    def __init__(self, scenario_id: int, user_id: int, redis = None):
        self.scenario_id = scenario_id
        self.user_id = user_id
        self.redis = redis or get_redis_connection("default")
        self.key = f"schedule:{scenario_id}:user:{user_id}"

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _load_json_field(self, field: str, default):
        """Загружает JSON из Redis"""
        raw = self.redis.hget(self.key, field)
        if raw is None:
            return default
        try:
            return json.loads(raw)
        except Exception:
            return default

    def _save_json_field(self, field: str, value):
        """Загружает JSON в Redis"""
        self.redis.hset(self.key, field, json.dumps(value))

    # -------------------------------------------------------------------------
    # Getters
    # -------------------------------------------------------------------------

    def get_updated(self) -> Dict[int, Dict[str, Any]]:
        data = self._load_json_field(self.FIELD_UPDATED, {})
        # Keys stored as strings → convert to int
        return {int(k): v for k, v in data.items()}

    def get_created(self) -> Dict[str, Dict[str, Any]]:
        return self._load_json_field(self.FIELD_CREATED, {})

    def get_deleted(self) -> List[int]:
        data = self._load_json_field(self.FIELD_DELETED, [])
        return list(map(int, data))

    # -------------------------------------------------------------------------
    # Setters / mutators
    # -------------------------------------------------------------------------

    def update_lesson(self, lesson_id: int, diff: Dict[str, Any]):
        """
        Добавляет изменения в занятия
        Отменяет удаление (если оно было)
        """
        updated = self.get_updated()
        deleted = self.get_deleted()

        if lesson_id in deleted:
            # lesson was previously removed — cancel deletion
            deleted.remove(lesson_id)
            self._save_json_field(self.FIELD_DELETED, deleted)

        # merge diffs
        current = updated.get(lesson_id, {})
        current.update(diff)
        updated[lesson_id] = current

        self._save_json_field(self.FIELD_UPDATED, updated)

    def create_lesson(self, new_id: str, data: Dict[str, Any]):
        """
        Create a new lesson (merged if exists).
        """
        created = self.get_created()
        current = created.get(new_id, {})
        current.update(data)
        created[new_id] = current
        self._save_json_field(self.FIELD_CREATED, created)

    def delete_lesson(self, lesson_id: int):
        """
        Mark lesson as deleted.
        Remove it from updated, and from created if present.
        """
        updated = self.get_updated()
        created = self.get_created()
        deleted = self.get_deleted()

        # Remove updated diff
        if lesson_id in updated:
            updated.pop(lesson_id)
            self._save_json_field(self.FIELD_UPDATED, updated)

        # Remove from created (rare case)
        created_keys = [k for k, v in created.items()
                        if str(v.get("id")) == str(lesson_id)]
        for k in created_keys:
            created.pop(k)
        self._save_json_field(self.FIELD_CREATED, created)

        # Add to deleted list
        if lesson_id not in deleted:
            deleted.append(lesson_id)
            self._save_json_field(self.FIELD_DELETED, deleted)

    # -------------------------------------------------------------------------
    # Очистка
    # -------------------------------------------------------------------------

    def clear_updated(self):
        self.redis.hdel(self.key, self.FIELD_UPDATED)

    def clear_created(self):
        self.redis.hdel(self.key, self.FIELD_CREATED)

    def clear_deleted(self):
        self.redis.hdel(self.key, self.FIELD_DELETED)

    def clear_all(self):
        self.redis.delete(self.key)

    # -------------------------------------------------------------------------
    # Вспомогательные функции
    # -------------------------------------------------------------------------

    def has_any_changes(self) -> bool:
        """Quick check for any changes in storage."""
        return bool(self.redis.hlen(self.key) > 0)

    def list_changes(self):
        """Unified dict view of all changes."""
        return {
            "updated": self.get_updated(),
            "created": self.get_created(),
            "deleted": self.get_deleted(),
        }