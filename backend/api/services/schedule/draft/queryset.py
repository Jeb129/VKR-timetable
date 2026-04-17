from django.db.models import QuerySet, Q
from api.services.redis.storage import RedisDraftStorage

class DraftFilters:
    """
    Отвечает за применение Django-like фильтров к объекту.
    """

    def __init__(self, filters=None):
        self.filters = filters or []

    def matches(self, obj):
        """
        Проверяет, проходит ли объект все фильтры и exclude.
        """
        for ftype, q_objects, lookups in self.filters:
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
        Оценивает lookup expr на объекте, включая overlay M2M через _prefetched_objects_cache.
        Поддерживает related__field__lookup.
        """

        LOOKUPS = {
            "exact": lambda a, b: a == b,
            "iexact": lambda a, b: str(a).lower() == str(b).lower(),
            "contains": lambda a, b: b in a if a is not None else False,
            "icontains": lambda a, b: str(b).lower() in str(a).lower() if a is not None else False,
            "in": lambda a, b: a in b if hasattr(b, '__contains__') else False,
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

        parts = expr.split("__")

        # Определяем lookup (contains, exact, in, id__in, ...)
        if parts[-1] in LOOKUPS:
            lookup = parts[-1]
            attr_parts = parts[:-1]
        else:
            lookup = "exact"
            attr_parts = parts

        current = obj

        # Получаем info о полях модели
        m2m_fields = {f.name for f in obj._meta.many_to_many}

        for i, attr in enumerate(attr_parts):

            # ---- M2M overlay через _prefetched_objects_cache ----
            if attr in m2m_fields and hasattr(obj, "_prefetched_objects_cache"):
                if attr in obj._prefetched_objects_cache:
                    current = obj._prefetched_objects_cache[attr]   # кешированный queryset
                else:
                    current = getattr(obj, attr).all()              # обычный queryset из БД

            # обычные поля / related поля 
            else:
                current = getattr(current, attr, None)

            if current is None:
                break

            # если это M2M queryset 
            if isinstance(current, QuerySet):
                # Если следующее поле — "id"
                if i < len(attr_parts) - 1 and attr_parts[i + 1] == "id":
                    ids = list(current.values_list("id", flat=True))

                    func = LOOKUPS.get(lookup, LOOKUPS["exact"])

                    if lookup == "exact":
                        return value in ids

                    if lookup == "in":
                        return any(v in ids for v in value)

                    # другие lookup'ы для id нам обычно не нужны
                    return False

                # Если lookup применяется к самому M2M (teachers__exact=[])
                if lookup in ("exact", "in"):
                    ids = list(current.values_list("id", flat=True))
                    return LOOKUPS[lookup](ids, value)

        # ---- простой lookup ----
        func = LOOKUPS.get(lookup, LOOKUPS["exact"])
        return func(current, value)
    

class DraftOverlayEngine:
    def __init__(self, model, storage: RedisDraftStorage):
        self.model = model
        self.storage = storage

        changes = storage.list_changes()

        self.updated = changes["updated"]
        self.created = changes["created"]
        self.deleted = set(changes["deleted"])

        # кеш метаданных модели
        self.m2m_fields = {
            f.name: f for f in model._meta.many_to_many
        }

    def build_created(self, pk, data):
        obj = self.model(
            id=None,
            **{
                f"{k}_id": v
                for k, v in data.items()
                if k not in self.m2m_fields
            }
        )

        for field in self.m2m_fields:
            if field in data:
                getattr(obj, field).set(data[field])

        return obj

    def created_objects(self):
        for pk, data in self.created.items():
            yield self.build_created(pk, data)

    def apply_update(self, obj):
        data = self.updated.get(obj.id, {})

        if not hasattr(obj, "_prefetched_objects_cache"):
            obj._prefetched_objects_cache = {}

        for field, value in data.items():

            if field in self.m2m_fields:
                rel_model = self.m2m_fields[field].remote_field.model

                obj._prefetched_objects_cache[field] = (
                    rel_model.objects.filter(id__in=value)
                )

            else:
                setattr(obj, f"{field}_id", value)

        return obj


    def apply_queryset(self, iterable, filters: DraftFilters):

        # если это QuerySet — используем iterator()
        if hasattr(iterable, "iterator"):
            base_iter = iterable.iterator()
        else:
            base_iter = iterable

        for obj in base_iter:

            if obj.id in self.deleted:
                continue

            if obj.id in self.updated:
                obj = self.apply_update(obj)

            if filters.matches(obj):
                yield obj

        for obj in self.created_objects():
            if filters.matches(obj):
                yield obj


class DraftLessonQuerySet(QuerySet):
    """
    QuerySet для подмешивания данных из Redis
    """
    # ---------------------------------------
    # Создание queryset
    # ---------------------------------------

    def __init__(self, *args, storage: RedisDraftStorage=None, scenario_id=None,**kwargs):
        super().__init__(*args,**kwargs)
        self.storage = storage
        self.scenario_id = scenario_id
        self.m2m_fields = {f.name: f for f in self.model._meta.many_to_many}
        self._draft_filters = []
        if scenario_id:
            self.query.add_q(Q(scenario_id=scenario_id))
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
        clone.updated = self.updated.copy()
        clone.created = self.created.copy()
        clone.deleted = self.deleted.copy()
        clone._draft_filters = self._draft_filters.copy()
        return clone
    
    # ---------------------------------------
    # Поиск и получение объектов
    # ---------------------------------------
    def get(self, *args, **kwargs):
        qs = self.filter(*args, **kwargs)

        engine = DraftOverlayEngine(self.model, self.storage)
        filters = DraftFilters(qs._draft_filters)

        iterator = engine.apply_queryset(
            super().filter(*args, **kwargs).iterator(),
            filters
        )

        try:
            obj = next(iterator)
        except StopIteration:
            raise self.model.DoesNotExist()

        try:
            next(iterator)
            raise self.model.MultipleObjectsReturned()
        except StopIteration:
            pass

        return obj
    
    
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
    

    def all(self):
        """
        Возвращает все объекты после применения draft-фильтров.
        """
        return self._clone()
    

    def filter(self, *args, **kwargs):
        """
        Переопределение .filter().
        Создаёт клон QuerySet, сохраняет текущие фильтры и добавляет новые.
        Не строит SQL, фильтрация выполняется в Python.
        """
        clone = self._clone()
        clone._draft_filters = self._draft_filters.copy()
        q_objects = list(args)  # Q-объекты
        lookups = kwargs.copy()  # обычные field=value
        clone._draft_filters.append(("filter", q_objects, lookups))
        return clone


    def exclude(self, *args, **kwargs):
        """
        Переопределение .exclude().
        Создаёт клон QuerySet, сохраняет текущие фильтры и добавляет exclude.
        """
        clone = self._clone()
        clone._draft_filters = self._draft_filters.copy()
        q_objects = list(args)  # Q-объекты
        lookups = kwargs.copy()  # обычные field=value
        clone._draft_filters.append(("exclude", q_objects, lookups))
        return clone

    # ---------------------------------------
    # Итерация и извлечение объектов
    # ---------------------------------------
   
    def __iter__(self):
        """
        Итератор. Вызывает iterator(), возвращает объекты по одному.
        """
        return self.iterator()


    def iterator(self, *args, **kwargs):
        base_qs = super().iterator(*args, **kwargs)

        if not self.storage:
            yield from base_qs
            return

        engine = DraftOverlayEngine(self.model,self.storage)
        filters = DraftFilters(self._draft_filters)

        yield from engine.apply_queryset(base_qs,filters)



       