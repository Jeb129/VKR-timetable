from django.db.models import QuerySet, Q
from api.models import Lesson
from api.services.redis.storage import RedisDraftStorage
from api.services.schedule.draft.proxy import DraftRelationProxy

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
        clone.updated = self.updated
        clone.created = self.created
        clone.deleted = self.deleted
        clone._draft_filters = self._draft_filters.copy()
        return clone
    
    # ---------------------------------------
    # Поиск и получение объектов
    # ---------------------------------------
    
    def get(self, *args, **kwargs):
        if "id" in kwargs:
            key = kwargs["id"]
            if key in self.deleted:
                raise Lesson.DoesNotExist()
            if key in self.created:
                return self._build_created_instance(key, self.created[key])
            if key in self.updated:
                lesson = self.model._default_manager.get(*args, **kwargs)
                return self._apply_update(lesson)
            
            return self.model._default_manager.get(*args, **kwargs)
    
    
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
        # Существующие объекты
        for lesson in super().iterator(*args, **kwargs):
            lid = lesson.id
            obj = None
            if lid in self.deleted:
                continue
            elif lid in self.updated:
                obj = self._apply_update(lesson)
            else:
                obj = lesson        

            if self._matches_all(obj):
                yield obj
            else:
                continue
        # Новые объекты
        for lid, data in self.created.items():
            obj = self._build_created_instance(lid, data)
            if self._matches_all(obj):
                yield obj
            else:
                continue   

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
            **{f"{k}_id": v for k, v in data.items() if k not in ("teachers", "study_groups")}
        )

        # M2M proxy
        for field in ("teachers", "study_groups"):
            if field in data:
                m2m_manager = getattr(obj, field)
                m2m_manager.set(data[field])
        return obj
      

    def _apply_update(self, obj):
        """
        Применяет обновлённые поля к объекту.
        """
        updated_fields = self.updated.get(obj.id, {})
        for field, value in updated_fields.items():
            if field in ("teachers", "study_groups"):
                # M2M пока не работает
                model = getattr(obj, field).model
                proxy = DraftRelationProxy(model, value)
                setattr(obj, f"_draft_{field}", proxy)
            else:
                setattr(obj, f"{field}_id", value)
        return obj


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
        parts = expr.split("__")
        if parts[-1] in LOOKUPS:
            lookup = parts[-1]
            attr_parts = parts[:-1]
        else:
            lookup = "exact"
            attr_parts = parts

        current = obj
        for attr in attr_parts:
            if hasattr(current, f"_draft_{attr}"):
                current = getattr(current, f"_draft_{attr}")
            else:
                current = getattr(current, attr, None)
            if current is None:
                break
        # ---------------------- M2M Пока не работает ----------------------
        # if isinstance(current, DraftRelationProxy):
        #     if lookup in ("exact", "in"):
        #         func = lambda a, b: getattr(b, "id", b) in a._ids if lookup == "in" else getattr(b, "id", b) in a._ids
        #     else:
        #         current = list(current)
        # ------------------------------------------------------------------
        if lookup not in LOOKUPS:
            lookup, value = "exact", value
        func = LOOKUPS[lookup]
        result = func(current, value)
        return result