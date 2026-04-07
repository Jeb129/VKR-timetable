import json
from uuid import uuid4
from pickletools import uint8
from typing import Dict, Any, List, Optional
from django_redis import get_redis_connection
from django.db import transaction

from api.models import Lesson
from api.services.schedule.draft.proxy import DraftRelationProxy_v2


class RedisDraftStorage:
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

    def create_lesson(self, data: Dict[str, Any], new_id: str = str(uuid4())):
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

    def commit_lesson(self, lesson: Lesson):
        """
        Применяет все черновые изменения к одному Lesson:
        - updated поля → update()
        - m2m поля → set()
        - если lesson помечен как deleted → удаляет
        - если lesson является new:* → создаёт реальный Lesson
        """

        lesson_id = lesson.id

        # ---------------------------
        # 1. Если удалён — удаляем
        # ---------------------------
        if lesson_id in self.deleted:
            lesson.delete()
            # Удаляем из redis
            self.remove_change(lesson_id)
            return None

        # ---------------------------
        # 2. Если обновляем существующий
        # ---------------------------
        if lesson_id in self.updated:
            diff = self.updated[lesson_id]

            # FK/обычные поля
            update_fields = {
                k: v for k, v in diff.items()
                if k not in ("teachers", "study_groups")
            }

            if update_fields:
                for field, value in update_fields.items():
                    setattr(lesson, field, value)
                lesson.save(update_fields=list(update_fields.keys()))

            # M2M
            if "teachers" in diff:
                lesson.teachers.set(diff["teachers"])

            if "study_groups" in diff:
                lesson.study_groups.set(diff["study_groups"])

            # Убираем diff из redis
            self.remove_change(lesson_id)

            return lesson

        # ---------------------------
        # 3. Если lesson был создан как new:ID
        # ---------------------------
        for key, data in self.created.items():
            if key == f"new:{lesson_id}":
                from api.models.schedule import Lesson as LessonModel

                new_lesson = LessonModel.objects.create(
                    scenario_id=self.scenario_id,
                    **{
                        k: v for k, v in data.items()
                        if k not in ("teachers", "study_groups")
                    }
                )

                if "teachers" in data:
                    new_lesson.teachers.set(data["teachers"])

                if "study_groups" in data:
                    new_lesson.study_groups.set(data["study_groups"])

                # Удаляем из redis запись new:*
                self.remove_new(key)
                return new_lesson

        # Если изменений нет — возвращаем как есть
        return lesson
   
    def commit_changes(self):
        """
        Применяет все черновые изменения к БД:
        - удаляет помеченные Lesson
        - обновляет изменённые Lesson
        - создаёт новые Lesson
        - обновляет M2M
        - очищает Redis
        """
        changes = self.list_changes()
        updated = changes["updated"]
        created = changes["created"]
        deleted = changes["deleted"]

        result_objects = []

        with transaction.atomic():
            # ----------------------------
            # 1. Удаление
            # ----------------------------
            if deleted:
                Lesson.objects.filter(id__in=deleted).delete()

            # ----------------------------
            # 2. Обновление существующих
            # ----------------------------
            for lid, diff in updated.items():
                try:
                    obj = Lesson.objects.get(id=lid)
                except Lesson.DoesNotExist:
                    continue

                simple_fields = {k: v for k, v in diff.items() if k not in ("teachers", "study_groups")}
                if simple_fields:
                    for field, value in simple_fields.items():
                        setattr(obj, f"{field}__id", value)
                    obj.save(update_fields=list(simple_fields.keys()))

                # M2M
                for m2m_field in ("teachers", "study_groups"):
                    if m2m_field in diff:
                        ids = diff[m2m_field]
                        if isinstance(ids, DraftRelationProxy_v2):
                            ids = list(ids._ids)
                        getattr(obj, m2m_field).set(ids)

                result_objects.append(obj)

                # ----------------------------
                # 3. Создание новых
                # ----------------------------
                for data in created.values():
                    obj = Lesson.objects.create(
                        scenario_id=self.scenario_id,
                        **{k: v for k, v in data.items() if k not in ("teachers", "study_groups")}
                    )

                    for m2m_field in ("teachers", "study_groups"):
                        if m2m_field in data:
                            ids = data[m2m_field]
                            if isinstance(ids, DraftRelationProxy_v2):
                                ids = list(ids._ids)
                            getattr(obj, m2m_field).set(ids)

                    result_objects.append(obj)

                # ----------------------------
                # 4. Очистка Redis
                # ----------------------------
                self.clear_all()

        return result_objects
    # def commit_changes(self):
    #     """
    #     Применяет все черновые изменения к БД:
    #     - удаляет помеченные Lesson
    #     - обновляет изменённые Lesson
    #     - создаёт новые Lesson
    #     - обновляет M2M
    #     - очищает Redis
        
    #     Возвращает список изменённых/созданных Lesson.
    #     """
    #     changes = self.list_changes()

    #     updated = changes["updated"]
    #     created = changes["created"]
    #     deleted = changes["deleted"]

    #     result_objects = []

    #     with transaction.atomic():

    #         # ----------------------------
    #         # 1. Удаление
    #         # ----------------------------
    #         if deleted:
    #             Lesson.objects.filter(id__in=deleted).delete()

    #         # ----------------------------
    #         # 2. Обновление существующих
    #         # ----------------------------
    #         for lid, diff in updated.items():
    #             try:
    #                 obj = Lesson.objects.get(id=lid)
    #             except Lesson.DoesNotExist:
    #                 continue

    #             # FK / обычные поля
    #             simple_fields = {
    #                 k: v for k, v in diff.items()
    #                 if k not in ("teachers", "study_groups")
    #             }

    #             if simple_fields:
    #                 for field, value in simple_fields.items():
    #                     setattr(obj, field, value)
    #                 obj.save(update_fields=list(simple_fields.keys()))

    #             # M2M
    #             if "teachers" in diff:
    #                 obj.teachers.set(diff["teachers"])
    #             if "study_groups" in diff:
    #                 obj.study_groups.set(diff["study_groups"])

    #             result_objects.append(obj)

    #         # ----------------------------
    #         # 3. Создание новых уроков
    #         # ----------------------------
    #         for new_key, data in created.items():
    #             obj = Lesson.objects.create(
    #                 scenario_id=self.scenario_id,
    #                 **{
    #                     k: v for k, v in data.items()
    #                     if k not in ("teachers", "study_groups")
    #                 }
    #             )

    #             # M2M
    #             if "teachers" in data:
    #                 obj.teachers.set(data["teachers"])
    #             if "study_groups" in data:
    #                 obj.study_groups.set(data["study_groups"])

    #             result_objects.append(obj)

    #         # ----------------------------
    #         # 4. Очистка Redis
    #         # ----------------------------
    #         self.clear_all()

    #     return result_objects
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