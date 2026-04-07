from django.db.models import QuerySet
from api.models import Lesson,StudyGroup,Teacher
from api.services.redis.storage import RedisDraftStorage
from api.services.schedule.draft.proxy import DraftRelationProxy_v2





class DraftLessonQuerySet_v2(QuerySet):
    def __init__(self, *args, storage: RedisDraftStorage=None, scenario_id=None,**kwargs):
        super().__init__(*args,**kwargs)
        self.storage = storage
        self.scenario_id = scenario_id
        self._draft_filters = []

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
        
    def _clone(self, **kwargs):
        clone = super()._clone(**kwargs)
        clone.storage = self.storage
        clone.scenario_id = self.scenario_id
        clone.updated = self.updated
        clone.created = self.created
        clone.deleted = self.deleted
        return clone
    def filter(self, *args, **kwargs):
        """
        Переопределение .filter().
        Создаёт клон QuerySet, сохраняет текущие фильтры и добавляет новые.
        Не строит SQL, фильтрация выполняется в Python.
        """
        clone = self._clone()
        clone._draft_filters = self._draft_filters.copy()
        clone._draft_filters.append(("filter", args, kwargs))
        return clone

    def exclude(self, *args, **kwargs):
        """
        Переопределение .exclude().
        Создаёт клон QuerySet, сохраняет текущие фильтры и добавляет exclude.
        """
        clone = self._clone()
        clone._draft_filters = self._draft_filters.copy()
        clone._draft_filters.append(("exclude", args, kwargs))
        return clone
    # ---------------------------------------
    # Итерация и извлечение объектов
    # ---------------------------------------
    def __iter__(self):
        """
        Итератор. Вызывает iterator(), возвращает объекты по одному.
        """
        return self.iterator()

    def all(self):
        """
        Возвращает все объекты после применения draft-фильтров.
        """
        return self._clone()

    def iterator(self):
        """
        Основной генератор объектов:
        1. Получает объекты из базы (super().iterator()).
        2. Объединяет с Redis (created/updated/deleted).
        3. Применяет python-фильтры (_draft_filters).
        """
        # 1. База
        db_objects = list(super().iterator())

        # 2. Соединяем данные
        objects = self._merge_objects(db_objects)

        # 3. Фильтруем по python
        for obj in self._apply_filters(objects):
            yield obj

    def first(self):
        """
        Возвращает первый объект после фильтрации.
        """
        for obj in self.iterator():
            return obj
        return None

    def last(self):
        """
        Возвращает последний объект после фильтрации.
        """
        all_objs = list(self.iterator())
        return all_objs[-1] if all_objs else None

    def exists(self):
        """
        Возвращает True, если есть хотя бы один объект после фильтрации.
        """
        for _ in self.iterator():
            return True
        return False

    def count(self):
        """
        Возвращает количество объектов после фильтрации.
        """
        return sum(1 for _ in self.iterator())
    

    # ---------------------------------------
    # Мерж БД и Redis
    # ---------------------------------------
    def _build_created_instance(self, data):
        """
        Преобразует словарь из Redis в объект Lesson с draft-proxy для M2M.
        """
        # Создаём базовый объект без сохранения
        obj = Lesson(
            id=None,
            scenario_id=self.scenario_id,
            **{k: v for k, v in data.items() if k not in ("teachers", "study_groups")}
        )

        # M2M proxy
        for field in ("teachers", "study_groups"):
            if field in data:
                # m2m_manager = getattr(Lesson, field)
                # m2m_manager.set(data[field])
                model = getattr(Lesson, field).rel.model
                setattr(obj, f"{field}", DraftRelationProxy(model, data[field]))
        return obj
    def _merge_objects(self, db_objects):
        """
        Объединяет объекты из БД и Redis.

        Правила:
        - deleted: исключаем объекты
        - updated: обновляем поля объектов из базы
        - created: добавляем новые объекты
        """
        merged = []

        # 1. Обновляем/исключаем объекты из БД
        for obj in db_objects:
            if obj.id in self.deleted:
                continue
            if obj.id in self.updated:
                obj = self._apply_update(obj)
            merged.append(obj)

        # создаём подготовленные объекты
        prepared_created = [self._build_created_instance(d) for d in self.created.values()]

        # добавляем в общий список
        merged.extend(prepared_created)
        return merged
    
    def _apply_update(self, obj):
        """
        Применяет обновлённые поля к объекту.
        """
        updated_fields = self.updated.get(obj.id, {})
        for field, value in updated_fields.items():
            if field in ("teachers", "study_groups"):
                # M2M подмена через proxy
                model = getattr(obj, field).model
                proxy = DraftRelationProxy(model, value)
                setattr(obj, f"{field}", proxy)
                # m2m_manager = getattr(Lesson, field)
                # m2m_manager.set(value)
            else:
                setattr(obj, field, value)
        return obj
    # def _apply_update(self, obj):
    #     """
    #     Применяет обновлённые поля к объекту.
    #     """
    #     updated_obj = self.updated[obj.id]
    #     for field in updated_obj._meta.fields:
    #         setattr(obj, field.attname, getattr(updated_obj, field.attname))
    #     return obj
    
    def get(self, *args, **kwargs):
        # new lessons?
        print("Вызван get в кастомном queryset\n", args, "\n",kwargs)
        if "id" in kwargs:
            key = kwargs["id"]
            print("Передан ключ id")
            if key in self.deleted:
                print("Изменение Удален")
                raise Lesson.DoesNotExist()
            if key in self.created:
                print("Изменение Создан")
                return self._build_created_instance(key, self.created[key])
            if key in self.updated:
                print("Изменение Обновлен")
                lesson = super().get(*args, **kwargs)
                return self._apply_update(lesson)
            
        print("Нет изменений")
        return super().get(*args, **kwargs)
    # ---------------------------------------
    # Применение фильтров
    # ---------------------------------------
    def _apply_filters(self, objects):
        """
        Применяет все фильтры и exclude из _draft_filters к списку объектов.
        """
        for obj in objects:
            if self._matches_all(obj):
                yield obj

    def _matches_all(self, obj):
        """
        Проверяет, проходит ли объект все фильтры и exclude.
        """
        for ftype, q_objects, lookups in self._draft_filters:
            passed = True

            # Q-объекты
            for q in q_objects:
                if not self._evaluate_q(obj, q):
                    passed = False
                    break

            # обычные lookups
            for expr, value in lookups.items():
                if not self._evaluate_expr(obj, expr, value):
                    passed = False
                    break

            if ftype == "exclude":
                passed = not passed

            if not passed:
                return False
        return True

    # ---------------------------------------
    # Evaluator (lookup + related)
    # ---------------------------------------
    def _evaluate_q(self, obj, q):
        """
        Рекурсивно оценивает Q-объект на python-объекте.
        """
        result = None
        for child in q.children:
            if isinstance(child, Q):
                val = self._evaluate_q(obj, child)
            else:
                expr, value = child
                val = self._evaluate_expr(obj, expr, value)

            if result is None:
                result = val
            elif q.connector == Q.AND:
                result = result and val
            else:  # OR
                result = result or val

        if q.negated:
            result = not result
        return result

    def _evaluate_expr(self, obj, expr, value):
        """
        Оценивает lookup expr на объекте, поддерживает related__field__lookup.
        """
        parts = expr.split("__")
        attr_parts = parts[:-1]
        lookup = parts[-1]

        # Попытка использовать стандартные lookup
        LOOKUPS = {
            "exact": lambda a, b: a == b,
            "iexact": lambda a, b: str(a).lower() == str(b).lower(),
            "contains": lambda a, b: b in a if a is not None else False,
            "icontains": lambda a, b: str(b).lower() in str(a).lower() if a is not None else False,
            "in": lambda a, b: a in b,
            "gt": lambda a, b: a > b,
            "gte": lambda a, b: a >= b,
            "lt": lambda a, b: a < b,
            "lte": lambda a, b: a <= b,
            "startswith": lambda a, b: str(a).startswith(b) if a is not None else False,
            "istartswith": lambda a, b: str(a).lower().startswith(str(b).lower()) if a is not None else False,
            "endswith": lambda a, b: str(a).endswith(b) if a is not None else False,
            "iendswith": lambda a, b: str(a).lower().endswith(str(b).lower()) if a is not None else False,
            "isnull": lambda a, b: (a is None) == b,
        }

        # Получаем значение поля, проходя по related
        current = obj
        for attr in attr_parts:
            # Если есть draft proxy, используем его
            if hasattr(current, f"_draft_{attr}"):
                current = getattr(current, f"_draft_{attr}")
            else:
                current = getattr(current, attr, None)
            if current is None:
                break

        # Если current — DraftRelationProxy, нужно проверять по id
        if isinstance(current, DraftRelationProxy_v2):
            if lookup in ("exact", "in"):
                func = lambda a, b: getattr(b, "id", b) in a._ids if lookup=="in" else getattr(b, "id", b) in a._ids
            else:
                # Для других lookups можно получить все объекты и проверять по Python
                current = list(current)
            
        # for attr in attr_parts:
        #     current = getattr(current, attr, None)
        #     if current is None:
        #         break

        # Если последний элемент не lookup, значит exact
        if lookup not in LOOKUPS:
            lookup, value = "exact", value
        func = LOOKUPS[lookup]
        return func(current, value)


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

    def __init__(self, *args, storage =None, scenario_id=None, base_manager=None, **kwargs):
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

        # В методе ошибка. В атрибуты устанавливаются данные из redis хотя тут не объекты а их id
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
                except:
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
            if key in self.deleted:
                raise Lesson.DoesNotExist()
            if key in self.created:
                return self.build_created_instance(key, self.created[key])

        lesson = super().get(*args, **kwargs)
        obj = self.apply_drafts(lesson)
        if obj is None:
            raise Lesson.DoesNotExist()
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
