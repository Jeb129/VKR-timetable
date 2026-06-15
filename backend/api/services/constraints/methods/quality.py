from numpy import less

from api.services.constraints.meta import BaseConstraint, constraint, ConstraintError
from api.services.schedule.context import ScheduleContext
from api.models import Lesson
from config.utils import get_cached_M2M


@constraint("group_daily_overload")
def group_daily_overload(lesson: Lesson, context: ScheduleContext, weight: int):
    ts = lesson.timeslot
    if not ts:
        return None

    violations = []
    study_groups = get_cached_M2M(lesson, "study_groups")
    for group in study_groups:
        chain = context.get_group_day_chain(group.id, ts.week_num, ts.day)
        hours = len(chain) * 2
        limit = getattr(group, "max_hours_per_day", 8) or 8
        if hours > limit:
            violations.append({"group": group, "current_hours": hours, "limit": limit})

    return (
        ConstraintError(
            name="group_daily_overload",
            message="У некоторых групп перегружен день",
            penalty=weight,
            data=violations,
        )
        if violations
        else None
    )


@constraint("teacher_daily_overload")
def teacher_daily_overload(lesson: Lesson, context: ScheduleContext, weight: int):
    ts = lesson.timeslot
    if not ts:
        return None

    violations = []
    teachers = get_cached_M2M(lesson, "teachers")
    for teacher in teachers:
        chain = context.get_teacher_day_chain(teacher.id, ts.week_num, ts.day)
        hours = len(chain) * 2
        limit = teacher.max_hours_per_day or 8
        if hours > limit:
            violations.append(
                {"teacher": teacher, "current_hours": hours, "limit": limit}
            )

    return (
        ConstraintError(
            name="teacher_daily_overload",
            message="У некоторых преподавателей перегружен день",
            penalty=weight,
            data=violations,
        )
        if violations
        else None
    )


@constraint("students_gap")
def students_gap(lesson: Lesson, context: ScheduleContext, weight: int):
    ts = lesson.timeslot
    if not ts:
        return None

    violations = []
    study_groups = get_cached_M2M(lesson, "study_groups")
    for group in study_groups:
        prev, nxt = context.get_group_neighbors(lesson, group.id)
        if prev and (ts.order_number - prev.timeslot.order_number > 1):
            violations.append({"group": group, "side": "before", "gap_with": prev})
        if nxt and (nxt.timeslot.order_number - ts.order_number > 1):
            violations.append({"group": group, "side": "after", "gap_with": nxt})

    return (
        ConstraintError(
            name="students_gap",
            message="У некоторых групп есть окно",
            penalty=weight * len(violations),
            data=violations,
        )
        if violations
        else None
    )


@constraint("building_clustering")
class BuildingClustering(BaseConstraint):
    def _build_soft(self, model, lesson_vars, context):
        penalties = []
        weight = self.config.weight
        num_bldgs = len(context.building_to_idx)

        # Проверяем пары занятий одного дня
        for (w, d), day_slots in self._get_day_map(context).items():
            # Для каждого учителя
            for t_id, l_ids in context.teacher_to_l_ids.items():
                relevant = [l_id for l_id in l_ids if l_id in lesson_vars]
                if len(relevant) < 2: continue
                
                for i in range(len(relevant)):
                    for j in range(i + 1, len(relevant)):
                        id1, id2 = relevant[i], relevant[j]
                        v1, v2 = lesson_vars[id1], lesson_vars[id2]
                        
                        # Булевы: оба занятия в этот день?
                        in_day1 = model.new_bool_var('')
                        in_day2 = model.new_bool_var('')
                        model.add_bool_or([model.new_bool_var('')]).only_enforce_if(in_day1) # ...условие слота
                        
                        # Упрощенная логика: Penalty если Building1 != Building2
                        # при условии, что они оба в один день (используем попарный штраф)
                        diff_bldg = model.new_bool_var(f'b_cl_{t_id}_{id1}_{id2}')
                        
                        b1 = model.new_int_var(0, num_bldgs, '')
                        b2 = model.new_int_var(0, num_bldgs, '')
                        model.add_element(v1.room_var, context.room_building_indices, b1)
                        model.add_element(v2.room_var, context.room_building_indices, b2)
                        
                        # Штрафуем, если (Slot1.day == Slot2.day) И (B1 != B2)
                        same_day = model.new_bool_var('')
                        # ... связь v1.slot_var и v2.slot_var (одна неделя и день)
                        
                        model.add(b1 != b2).only_enforce_if([diff_bldg, same_day])
                        penalties.append(diff_bldg * weight)
        return penalties
    def building_clustering(lesson: Lesson, context: ScheduleContext, weight: int):
        ts = lesson.timeslot
        if not ts:
            return None

        violations = []
        study_groups = get_cached_M2M(lesson, "study_groups")
        for group in study_groups:
            chain = context.get_group_day_chain(group.id, ts.week_num, ts.day)
            buildings = {
                l.classroom.building
                for l in chain
                if l.classroom and not l.classroom.is_virtual
            }
            if len(buildings) > 1:
                violations.append({"group": group, "buildings": list(buildings)})

        return (
            ConstraintError(
                name="building_clustering",
                message="Некоторым группам / преподавателям придется менять корпус",
                penalty=weight * len(violations),
                data=violations,
            )
            if violations
            else None
        )


@constraint("lesson_persistence_sort")
def lesson_persistence_sort(lesson: Lesson, context: ScheduleContext, weight: int):
    ts = lesson.timeslot
    # Если нет слота или не указана длительность — проверять нечего
    if not ts or not lesson.whole_weeks:
        return None

    current_weeks = lesson.whole_weeks
    violations = []

    # 1. Проверяем цепочки групп
    study_groups = get_cached_M2M(lesson, "study_groups")
    for group in study_groups:
        chain = context.get_group_day_chain(group.id, ts.week_num, ts.day)

        # Ищем занятия в тот же день, которые длятся дольше
        longer_before = [
            l
            for l in chain
            if l.timeslot.order_number < ts.order_number
            and (l.whole_weeks or 0) > current_weeks
        ]
        longer_after = [
            l
            for l in chain
            if l.timeslot.order_number > ts.order_number
            and (l.whole_weeks or 0) > current_weeks
        ]

        if longer_before and longer_after:
            violations.append(
                {
                    "entity_type": "group",
                    "entity": group,
                    "longer_before": longer_before[
                        0
                    ],  # Для примера берем первое попавшееся
                    "longer_after": longer_after[0],
                }
            )

    # 2. Проверяем цепочки преподавателей
    teachers = get_cached_M2M(lesson, "teachers")
    for teacher in teachers:
        chain = context.get_teacher_day_chain(teacher.id, ts.week_num, ts.day)

        longer_before = [
            l
            for l in chain
            if l.timeslot.order_number < ts.order_number
            and (l.whole_weeks or 0) > current_weeks
        ]
        longer_after = [
            l
            for l in chain
            if l.timeslot.order_number > ts.order_number
            and (l.whole_weeks or 0) > current_weeks
        ]

        if longer_before and longer_after:
            violations.append(
                {
                    "entity_type": "teacher",
                    "entity": teacher,
                    "longer_before": longer_before[0],
                    "longer_after": longer_after[0],
                }
            )

    if violations:
        return ConstraintError(
            name="lesson_persistence_sort",
            penalty=weight,
            message=(f"Занятие зажато между более длинными курсами."),
            data=violations,
        )

    return None


@constraint("morning_preference")
class MorningPreference(BaseConstraint):
    def _build_soft(self, model, lesson_vars, context):
        penalties = []
        weight = self.config.weight
        
        # Создаем карту: индекс слота -> штраф (order_number - 1)
        # Пара 1 (order 1) -> штраф 0
        # Пара 6 (order 6) -> штраф 5 * weight
        slot_penalty_map = [
            (context.idx_to_slot[i].order_number - 1) 
            for i in range(len(context.idx_to_slot))
        ]

        for l_id, v in lesson_vars.items():
            l_penalty = model.new_int_var(0, 10 * weight, f'morn_{l_id}')
            model.add_element(v.slot_var, slot_penalty_map, l_penalty)
            penalties.append(l_penalty * weight)
            
        return penalties
    
    def check(self,lesson: Lesson, context: ScheduleContext):
        ts = lesson.timeslot
        if not ts or ts.order_number == 1:
            return None
        return ConstraintError(
            name="morning_preference",
            message="занятия не в начале дня",
            penalty=(ts.order_number - 1) * self.config.weight,
            data={"order": ts.order_number},
        )


@constraint("teachers_gap")
def teachers_gap(lesson: Lesson, context: ScheduleContext, weight: int):
    ts = lesson.timeslot
    if not ts:
        return None

    violations = []
    teachers = get_cached_M2M(lesson, "teachers")
    for teacher in teachers:
        prev, nxt = context.get_teacher_neighbors(lesson, teacher.id)
        if prev and (ts.order_number - prev.timeslot.order_number > 1):
            violations.append({"teacher": teacher, "side": "before", "gap_with": prev})
        if nxt and (nxt.timeslot.order_number - ts.order_number > 1):
            violations.append({"teacher": teacher, "side": "after", "gap_with": nxt})

    return (
        ConstraintError(
            name="teachers_gap",
            message="У некоторых преподавателей есть окно",
            penalty=weight * len(violations),
            data=violations,
        )
        if violations
        else None
    )


# @constraint("teacher_weekly_overload")
def teacher_weekly_overload(lesson: Lesson, context: ScheduleContext, weight: int):
    violations = []
    teachers = get_cached_M2M(lesson, "teachers")
    for teacher in teachers:
        hours = context.get_teacher_weekly_hours(teacher.id)
        limit = teacher.max_hours_per_week or 36
        if hours > limit:
            violations.append({"teacher": teacher, "hours": hours, "limit": limit})

    return (
        ConstraintError(
            name="teacher_weekly_overload",
            message="У некоторых преподавателей перегружена неделя",
            penalty=weight,
            data=violations,
        )
        if violations
        else None
    )


# @constraint("group_weekly_overload")
def group_weekly_overload(lesson: Lesson, context: ScheduleContext, weight: int):
    violations = []
    study_groups = get_cached_M2M(lesson, "study_groups")
    for group in study_groups:
        hours = context.get_group_weekly_hours(group.id)
        limit = group.max_hours_per_week or 36
        if hours > limit:
            violations.append({"group": group, "hours": hours, "limit": limit})

    return (
        ConstraintError(
            name="group_weekly_overload",
            message="У некоторых групп перегружена неделя",
            penalty=weight,
            data=violations,
        )
        if violations
        else None
    )
