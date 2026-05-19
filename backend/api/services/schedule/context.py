from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from api.models import Lesson, BuildingTravelTime, Timeslot
from api.services.drafts.queryset import DraftFilters

@dataclass
class ScheduleContext:
    """
    Класс предназначен для индексации данных по занятиям в сценарии.
    Используется для ускорения проверок при редактировании / генерации
    """
    # Метаданные
    scenario_id: int

    # Основные данные
    lessons: List[Lesson] = field(default_factory=list)
    
    # Индексы для поиска пересечений: (entity_id, timeslot_id)
    teacher_lookup: Dict[Tuple[int, int], List[Lesson]] = field(default_factory=lambda: defaultdict(list))
    group_lookup: Dict[Tuple[int, int], List[Lesson]] = field(default_factory=lambda: defaultdict(list))
    classroom_lookup: Dict[Tuple[int, int], List[Lesson]] = field(default_factory=lambda: defaultdict(list))

    # Дневные цепочки: (entity_id, week, day)
    teacher_day_chains: Dict[Tuple[int, int, int], List[Lesson]] = field(default_factory=lambda: defaultdict(list))
    group_day_chains: Dict[Tuple[int, int, int], List[Lesson]] = field(default_factory=lambda: defaultdict(list))

    # Справочник времени перемещений: {(b1_id, b2_id): minutes}
    travel_map: Dict[Tuple[int, int], int] = field(default_factory=dict)
    # Справочник времени слотов: {slot_id: (start_mins, end_mins)}
    slot_times: Dict[int, Tuple[int, int]] = field(default_factory=dict)

    # --- Работа с индексами ---
    
    def _load_from_db(self):
        self.lessons = list(
                Lesson.objects.filter(scenario_id=self.scenario_id)
                .select_related(
                    "timeslot", 
                    "classroom", 
                    "classroom__building", 
                    "discipline", 
                    "lesson_type"
                )
                .prefetch_related("teachers", "study_groups")
            )
        
    def _index_metadata(self):
        """Загружает вспомогательные справочники из БД"""
        
        # 1. Индексируем время перемещений
        # Т.к. перемещение симметрично в твоем фильтре, пишем в обе стороны
        travels = BuildingTravelTime.objects.all()
        for t in travels:
            self.travel_map[(t.from_building_id, t.to_building_id)] = t.travel_time_minutes
            self.travel_map[(t.to_building_id, t.from_building_id)] = t.travel_time_minutes

        # 2. Индексируем время слотов (переводим Time в минуты с начала дня)
        slots = Timeslot.objects.all()
        for s in slots:
            start_m = s.time_start.hour * 60 + s.time_start.minute
            end_m = s.time_end.hour * 60 + s.time_end.minute
            self.slot_times[s.id] = (start_m, end_m)
    def _sort_chains(self):
        for chain in self.teacher_day_chains.values():
            chain.sort(key=lambda x: x.timeslot.order_number)
        
        for chain in self.group_day_chains.values():
            chain.sort(key=lambda x: x.timeslot.order_number)

    def _index_lesson(self, lesson: Lesson):
        ts = lesson.timeslot
        if not ts: return

        # Преподаватели
        for teacher in lesson.teachers.all():
            self.teacher_lookup[(teacher.id, ts.id)].append(lesson)
            self.teacher_day_chains[(teacher.id, ts.week_num, ts.day)].append(lesson)

        # Группы
        for group in lesson.study_groups.all():
            self.group_lookup[(group.id, ts.id)].append(lesson)
            self.group_day_chains[(group.id, ts.week_num, ts.day)].append(lesson)

        # Аудитории
        if lesson.classroom_id:
            self.classroom_lookup[(lesson.classroom_id, ts.id)].append(lesson)

    def _unindex_lesson(self, lesson: Lesson):
        """Удаляет занятие из всех lookup-таблиц"""
        ts = lesson.timeslot
        if not ts: return

        for t in self._get_cached(lesson,"teachers"):
            key = (t.id, ts.id)
            if lesson in self.teacher_lookup[key]: self.teacher_lookup[key].remove(lesson)
            day_key = (t.id, ts.week_num, ts.day)
            if lesson in self.teacher_day_chains[day_key]: self.teacher_day_chains[day_key].remove(lesson)

        for g in self._get_cached(lesson,"study_groups"):
            key = (g.id, ts.id)
            if lesson in self.group_lookup[key]: self.group_lookup[key].remove(lesson)
            day_key = (g.id, ts.week_num, ts.day)
            if lesson in self.group_day_chains[day_key]: self.group_day_chains[day_key].remove(lesson)

        if lesson.classroom_id:
            key = (lesson.classroom_id, ts.id)
            if lesson in self.classroom_lookup[key]: self.classroom_lookup[key].remove(lesson)

    def rebuild_indexes(self):
        """Полная пересборка всех индексов"""
        self.teacher_lookup.clear()
        self.group_lookup.clear()
        self.classroom_lookup.clear()
        self.teacher_day_chains.clear()
        self.group_day_chains.clear()

        for lesson in self.lessons:
            self._index_lesson(lesson)

        self._sort_chains()


    def __post_init__(self):
        if not self.lessons:
            self._load_from_db()
        self.rebuild_indexes()
        self._index_metadata()

    def _get_cached(self, lesson: Lesson,field:str):
        """Получение M2M связей для занятия без вызова менеджера (без необходимости)"""
        # Сначала проверяем кэш
        cache = getattr(lesson, '_prefetched_objects_cache', {})
        if field in cache:
            return cache[field]
        
        # Если объекта нет в кэше и нет ID (новый объект), возвращаем пустой список
        if not lesson.pk:
            return []
            
        # Если ID есть, но кэша нет — обычный запрос
        return getattr(lesson,field).all()

    def update_lesson_location(self, lesson: Lesson, new_timeslot, new_classroom):
        """Обновление занятия из индекса"""
        # 1. Удаляем из старых индексов
        self._unindex_lesson(lesson)
        
        # 2. Обновляем объект
        lesson.timeslot = new_timeslot
        lesson.timeslot_id = new_timeslot.id if new_timeslot else None
        lesson.classroom = new_classroom
        lesson.classroom_id = new_classroom.id if new_classroom else None

        # 3. Добавляем в новые индексы
        self._index_lesson(lesson)
        
        # 4. Сортируем только затронутые цепочки
        ts = lesson.timeslot
        for t in self._get_cached(lesson,"teachers"):
            self.teacher_day_chains[(t.id, ts.week_num, ts.day)].sort(key=lambda x: x.timeslot.order_number)
        for g in self._get_cached(lesson,"study_groups"):
            self.group_day_chains[(g.id, ts.week_num, ts.day)].sort(key=lambda x: x.timeslot.order_number)

    # --- QuerySet подобный поиск ---
    def filter(self, *args, **kwargs) -> List[Lesson]:
        """Фильтрация занятий в памяти контекста (аналог QuerySet.filter)"""
        # Создаем структуру фильтров, которую ожидает DraftFilters: (тип, Q-объекты, lookup-словарь)
        f = DraftFilters([("filter", list(args), kwargs)])
        return [l for l in self.lessons if f.matches(l)]

    def exclude(self, *args, **kwargs) -> List[Lesson]:
        """Исключение занятий в памяти контекста (аналог QuerySet.exclude)"""
        f = DraftFilters([("exclude", list(args), kwargs)])
        return [l for l in self.lessons if f.matches(l)]

    def get(self, **kwargs) -> Optional[Lesson]:
        """Поиск одного занятия в памяти (аналог QuerySet.get)"""
        results = self.filter(**kwargs)
        if len(results) > 1:
            raise ValueError(f"get() returned more than one Lesson. Found {len(results)}.")
        if len(results) == 0:
            return None
        return results[0]

    def get_by_id(self, lesson_id: int | str) -> Optional[Lesson]:
        """Поиск конкретного занятия в индексе. Быстрее чем get, т.к. не пересобирает список"""
        for l in self.lessons:
            if str(l.id) == str(lesson_id):
                return l
        return None
    
    # --- Поиск по индексам ---
    def get_teacher_day_chain(self, t_id: int, week: int, day: int) -> List[Lesson]:
        return self.teacher_day_chains.get((t_id, week, day), [])

    def get_group_day_chain(self, g_id: int, week: int, day: int) -> List[Lesson]:
        return self.group_day_chains.get((g_id, week, day), [])

    # --- Соседи (для окон и перемещений) ---
    def get_teacher_neighbors(self, lesson: Lesson, t_id: int) -> Tuple[Optional[Lesson], Optional[Lesson]]:
        ts = lesson.timeslot
        chain = self.get_teacher_day_chain(t_id, ts.week_num, ts.day)
        return self._extract_neighbors(chain, lesson)

    def get_group_neighbors(self, lesson: Lesson, g_id: int) -> Tuple[Optional[Lesson], Optional[Lesson]]:
        ts = lesson.timeslot
        chain = self.get_group_day_chain(g_id, ts.week_num, ts.day)
        return self._extract_neighbors(chain, lesson)

    # --- Нагрузка ---
    def get_teacher_weekly_hours(self, t_id: int) -> int:
        # Суммируем все часы (1 пара = 2 часа) и делим на 2 недели
        total_hours = sum(2 for l in self.lessons if any(t.id == t_id for t in l.teachers.all()))
        return total_hours // 2

    def get_group_weekly_hours(self, g_id: int) -> int:
        total_hours = sum(2 for l in self.lessons if any(g.id == g_id for g in l.study_groups.all()))
        return total_hours // 2

    # --- Внутренний хелпер ---
    def _extract_neighbors(self, chain: List[Lesson], target: Lesson) -> Tuple[Optional[Lesson], Optional[Lesson]]:
        try:
            idx = chain.index(target)
            prev = chain[idx - 1] if idx > 0 else None
            nxt = chain[idx + 1] if idx < len(chain) - 1 else None
            return prev, nxt
        except ValueError:
            return None, None