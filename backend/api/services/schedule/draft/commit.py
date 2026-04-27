from typing import Dict, Any, List
from django.db import transaction

from api.models import Lesson
from api.services.redis.storage import RedisDraftStorage


# 1. Сохранение всех изменений сценария
def commit_scenario(storage: RedisDraftStorage):
    """
    Применяет все черновые изменения к БД:
    - обновляет существующие Lesson
    - создаёт новые Lesson
    - удаляет помеченные
    - очищает Redis
    """
    drafts = storage.list_changes()
    removed_ids = drafts.get("removed", [])

    with transaction.atomic():

        # 1. Удаляем занятия
        if removed_ids:
            Lesson.objects.filter(id__in=removed_ids).delete()

        # 2. Обновляем существующие занятия
        for key, diff in drafts.items():
            if key.startswith("new:") or key == "removed":
                continue

            lesson_id = int(key)
            Lesson.objects.filter(id=lesson_id).update(**_extract_update_fields(diff))

        # 3. Создаём новые занятия
        for key, data in drafts.items():
            if not key.startswith("new:"):
                continue

            lesson = Lesson(
                scenario_id=storage.scenario_id,
                discipline_id=data["discipline"],
                lesson_type_id=data["lesson_type"],
                timeslot_id=data.get("timeslot"),
                classroom_id=data.get("classroom"),
            )
            lesson.save()

            # M2M:
            teachers = data.get("teachers", [])
            groups = data.get("study_groups", [])
            if teachers:
                lesson.teachers.set(teachers)
            if groups:
                lesson.study_groups.set(groups)

    # 4. Полная очистка сессии
    storage.clear()


# 2. Сохранение отдельного занятия
def commit_lesson(storage: RedisDraftStorage, lesson_id: int):
    """
    Применяет изменения конкретного Lesson из Redis в БД.
    """
    diff = storage.get_lesson(str(lesson_id))
    if not diff:
        return

    with transaction.atomic():
        Lesson.objects.filter(id=lesson_id).update(**_extract_update_fields(diff))

    # Удаляем diff
    storage.delete_lesson_diff(lesson_id)


# 3. Откат одного занятия
def rollback_lesson(storage: RedisDraftStorage, lesson_id: int):
    """
    Удаляет diff и пометку removed для одного Lesson.
    """
    storage.delete_lesson_diff(lesson_id)

    removed = storage.get_removed()
    if lesson_id in removed:
        storage.unmark_removed(lesson_id)


# 4. Откат нескольких занятий
def rollback_many(storage: RedisDraftStorage, lesson_ids: List[int]):
    for lesson_id in lesson_ids:
        rollback_lesson(storage, lesson_id)


# 5. Откат всей сессии
def rollback_all(storage: RedisDraftStorage):
    storage.clear()


# Вспомогательная функция
def _extract_update_fields(diff: Dict[str, Any]) -> Dict[str, Any]:
    """
    Оставляем только поля, которые действительно изменяются.
    """
    allowed_keys = {"timeslot", "classroom"}
    return {key + "_id": value for key, value in diff.items() if key in allowed_keys}
