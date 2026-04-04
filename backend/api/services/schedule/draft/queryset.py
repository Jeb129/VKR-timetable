from django.db.models import QuerySet
from api.models import Lesson

class DraftRelationProxy:
    """
    Простая прокси для M2M в черновиках.
    Принимает список id и возвращает queryset по ним.
    """
    def __init__(self, model, ids):
        self.model = model
        self.ids = ids

    def all(self):
        return self.model.objects.filter(id__in=self.ids)

    def __iter__(self):
        return iter(self.all())

    def __len__(self):
        return self.all().count()


class DraftLessonQuerySet(QuerySet):
    """
    Подмешивает изменения из RedisDraftStorage.
    """

    def __init__(self, *args, storage=None, scenario_id=None, base_manager=None, **kwargs):
        # print("storage is none?",storage is None)
        super().__init__(*args,**kwargs)
        self.storage = storage
        self.scenario_id = scenario_id

        # Кешируем diff
        if storage is not None:
            changes = storage.list_changes()
            self.updated = changes["updated"]
            self.created = changes["created"]
            self.deleted = set(changes["deleted"])
        else:
            # пустые состояния, чтобы queryset работал пока его не подменили
            self.updated = {}
            self.created = {}
            self.deleted = set()

        if base_manager:
            self._updated_base_cache = {
                obj.id: obj for obj in base_manager.filter(id__in=self.updated)
                }
        else:
            self._updated_base_cache = []
    
    def _clone(self, **kwargs):
        clone = super()._clone(**kwargs)
        clone.storage = self.storage
        clone.scenario_id = self.scenario_id
        clone.updated = self.updated
        clone.created = self.created
        clone.deleted = self.deleted
        return clone

    # ------------------------------------------------------------------
    # Вспомогательная функция: применяет diff к lesson
    # ------------------------------------------------------------------
    def apply_drafts(self, lesson):
        lesson_id = lesson.id
        # Обновление существующего занятия
        if lesson_id in self.updated:
            diff = self.updated[lesson_id]
            for field, value in diff.items():
                if field in ("teachers", "study_groups"):
                    # M2M подмена на proxy
                    model = getattr(lesson, field).model
                    proxy = DraftRelationProxy(model, value)
                    setattr(lesson, f"_draft_{field}", proxy)
                else:
                    setattr(lesson, field, value)

        return lesson

    # ------------------------------------------------------------------
    # Перегружаем iterator
    # ------------------------------------------------------------------
    def build_created_instance(self, key, data):
        """
        Создаём временный Lesson (без сохранения).
        """
        base_fields = {
            k: v for k, v in data.items()
            if k not in ("teachers", "study_groups")
        }
        obj = Lesson(
            id=None,
            scenario_id=self.scenario_id,
            **base_fields
        )
        # подмешиваем M2M как proxy
        if "teachers" in data:
            model = Lesson.teachers.rel.model
            obj.teachers = DraftRelationProxy(model, data["teachers"])

        if "study_groups" in data:
            model = Lesson.study_groups.rel.model
            obj.study_groups = DraftRelationProxy(model, data["study_groups"])

        return obj
    def __iter__(self):
        """
        Гарантируем, что именно наш iterator() используется.
        """
        return self.iterator()


    def _fetch_all(self):
        """
        Запрещаем Django использовать стандартный кешированный fetch_all,
        заставляя его идти через iterator() каждый раз.
        """
        if self._result_cache is None:
            self._result_cache = list(self.iterator())
        self._prefetch_related_objects()
    

    def iterator(self, *args, **kwargs):
        # updated_ids = self.updated.keys()
        # deleted_ids = self.deleted

        for lesson in super().iterator(*args, **kwargs):
            lid = lesson.id
            # Удалён?
            if lid in self.deleted:
                continue
            # Обновлён? Не отдаём оригинальный, отдаём измененный ныиже
            if lid in self.updated:
                continue

            yield lesson
        if self._updated_base_cache:
            for lid, _ in self.updated.items():
                # lesson из базы
                try:
                    base = self._updated_base_cache.get(lid)
                except self.model.DoesNotExist:
                    continue  # если базы нет — странно, но пропускаем

                patched = self.apply_drafts(base)
                yield patched

        # Созданные (pk нет)
        for lid, data in self.created.items():
            yield self.build_created_instance(lid, data)


    # ------------------------------------------------------------------
    def get(self, *args, **kwargs):
        # new lessons?
        if "id" in kwargs:
            key = kwargs["id"]
            if key in self.created:
                return self.build_created_instance(key, self.created[key])

        lesson = super().get(*args, **kwargs)
        obj = self.apply_drafts(lesson)
        if obj is None:
            raise self.model.DoesNotExist()
        return obj
        # return super().get(*args, **kwargs)
    
    def count(self):
        base = super().count()
        base -= len(self.deleted)
        base += len(self.created)
        return base
    
    def exists(self):
        if super().exists():
            # но могут быть все удалённые — нужно проверить iterator
            for _ in self.iterator():
                return True
            return False

        # но если есть created — true
        return bool(self.created)
