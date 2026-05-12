import json
from turtle import pen
from typing import Any, Dict, List
from uuid import uuid4

from django_redis import get_redis_connection


class ScheduleDraftStorage:
    """
    Хранилище черновиков расписания в Redis.

    Структура ключа:
        schedule:{scenario_id}:user:{user_id}

    Структура данных в Redis (hash):
        updated -> JSON object {lesson_id: ORM object}
        created -> JSON object {new_uuid: ORM object}
        deleted -> JSON array [lesson_ids]
    """

    FIELD_UPDATED = "updated"
    FIELD_CREATED = "created"
    FIELD_DELETED = "deleted"

    def __init__(self, scenario_id: int, user_id: int, redis=None):
        self.scenario_id = scenario_id
        self.user_id = user_id
        self.redis = redis or get_redis_connection("default")
        self.key = f"schedule:{scenario_id}:user:{user_id}"

    def __str__(self):
        return f"Черновик UserID:{self.user_id}, ScenarioID:{self.scenario_id}"

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
        return self._load_json_field(self.FIELD_UPDATED, {})
        # Keys stored as strings → convert to int
        # return {k: v for k, v in data.items()}

    def get_created(self) -> Dict[str, Dict[str, Any]]:
        return self._load_json_field(self.FIELD_CREATED, {})

    def get_deleted(self) -> List[str]:
        data = self._load_json_field(self.FIELD_DELETED, [])
        return list(map(str,data))

    # -------------------------------------------------------------------------
    # Setters / mutators
    # -------------------------------------------------------------------------

    def update_object(self, obj_id: str, diff: Dict[str, Any]):
        """
        Добавляет изменения в занятия
        Отменяет удаление (если оно было)
        """
        obj_id = str(obj_id)
        self.clear_deleted(obj_id)

        updated = self.get_updated()
        current = updated.get(obj_id, {})
        
        for key, value in diff.items():
            current[key] = value

        if current:
            updated[obj_id] = current
            self._save_json_field(self.FIELD_UPDATED, updated)

    def create_object(self, data: Dict[str, Any], new_id: str = str(uuid4())):
        """
        Создает новое занятие в хранилище черновика.
        Заменяет update_object для несохраненных в бд объектов
        """
        created = self.get_created()
        current = created.get(new_id, {})
        current.update(data)
        if current:
            created[new_id] = current
            self._save_json_field(self.FIELD_CREATED, created)
            return new_id
        else:
            return None

    def delete_object(self, obj_id: str):
        """
        Помечает объект на удаление
        """
        obj_id = str(obj_id)
        # Remove updated diff
        self.clear_updated(obj_id)

        # Remove from created (rare case)
        self.clear_created(obj_id)

        # Add to deleted list
        deleted = self.get_deleted()
        if obj_id not in deleted:
            deleted.append(obj_id)
            self._save_json_field(self.FIELD_DELETED, deleted)

    # -------------------------------------------------------------------------
    # Очистка
    # -------------------------------------------------------------------------

    def clear_updated(self, obj_id:str = None, key:str = None):
        if obj_id is None:
            self.redis.hdel(self.key, self.FIELD_UPDATED)
            return True
        
        obj_id =str(obj_id)
        updated = self.get_updated()
        if obj_id not in updated:
            return False
        
        if key is not None:
            current = updated.get(obj_id, {})
            del current[key]
            updated[obj_id] = current
        else:
            del updated[obj_id]

        self._save_json_field(self.FIELD_UPDATED, updated)
        return True
            

    def clear_created(self, obj_id: str = None):
        if obj_id is None:
            self.redis.hdel(self.key, self.FIELD_CREATED)
            return True
        
        obj_id =str(obj_id)
        created = self.get_created()
        if obj_id not in created.keys():
            return False
        
        del created[obj_id]
        self._save_json_field(self.FIELD_CREATED, created)
        return True

    def clear_deleted(self, obj_id:str = None):
        if obj_id is None:
            self.redis.hdel(self.key, self.FIELD_DELETED)
            return True
        
        obj_id =str(obj_id)
        deleted = self.get_deleted()
        if obj_id not in deleted:
            return False
        
        deleted.remove(obj_id)
        self._save_json_field(self.FIELD_DELETED, deleted)
        return True


    def clear_object(self, obj_id):
        upd = self.clear_updated(obj_id)
        crt = self.clear_created(obj_id)
        rem = self.clear_deleted(obj_id)
        return upd or crt or rem

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
