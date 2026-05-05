from dataclasses import dataclass, field
from typing import Any, Dict, List, Set, Optional
from api.models import BuildingTravelTime, Lesson

@dataclass
class ScheduleContext:
    """
    Объект, который готовится ОДИН РАЗ перед запуском всех проверок.
    Содержит проиндексированные данные для мгновенного поиска.
    """
    lessons: List[Any]
    # Индексы для быстрого поиска: (timeslot_id) -> [list of lessons]
    by_timeslot: Dict[int, List[Any]] = field(default_factory=dict)
    # (teacher_id, timeslot_id) -> [list of lessons]
    teacher_occupation: Dict[tuple, List[Any]] = field(default_factory=dict)
    # (group_id, timeslot_id) -> [list of lessons]
    group_occupation: Dict[tuple, List[Any]] = field(default_factory=dict)
    # Матрица расстояний между корпусами: (b1_id, b2_id) -> minutes
    travel_matrix: Dict[tuple, int] = field(default_factory=dict)

    @classmethod
    def build(cls, scenario_id):
        # ОДИН запрос со всеми нужными связями
        lessons = list(Lesson.objects.filter(scenario_id=scenario_id).select_related(
            'timeslot', 'classroom', 'classroom__building', 'discipline', 'lesson_type'
        ).prefetch_related('teachers', 'study_groups'))

        ctx = cls(lessons=lessons)
        
        # Индексируем всё в память
        for l in lessons:
            ts_id = l.timeslot_id
            if not ts_id: continue

            ctx.by_timeslot.setdefault(ts_id, []).append(l)
            
            for t in l.teachers.all():
                ctx.teacher_occupation.setdefault((t.id, ts_id), []).append(l)
            
            for g in l.study_groups.all():
                ctx.group_occupation.setdefault((g.id, ts_id), []).append(l)
        
        # Предзагрузка матрицы перемещений
        for tt in BuildingTravelTime.objects.all():
            ctx.travel_matrix[(tt.from_building_id, tt.to_building_id)] = tt.travel_time_minutes
            
        return ctx