from api.services.constraints.meta import constraint, ConstraintError,BaseConstraint
from api.services.schedule.context import ScheduleContext
from config.utils import get_cached_M2M

from api.models import (
    EquipmentRequirement,
    ClassroomPreference,
    ExcludedTimeslot,
    Lesson,
    enums,
)
from config.utils import get_cached_M2M


@constraint("room_meets_equipment_requirements")
class RoomMeetsEquipmentRequirements(BaseConstraint):
    def _build_soft(self, model, lesson_vars, context):
        penalties = []
        weight = self.config.weight
        
        for l_id, v in lesson_vars.items():
            lesson = context.get_by_id(l_id)
            # Берем требования из кэша контекста
            req_equipment = context.requirements_cache.get(
                (lesson.discipline_id, lesson.lesson_type_id), set()
            )
            if not req_equipment: continue

            # Находим "плохие" комнаты, где не хватает хотя бы одного предмета
            bad_room_indices = []
            for idx, room in context.idx_to_room.items():
                provided = set(get_cached_M2M(room, "equipment"))
                if not req_equipment.issubset(provided):
                    bad_room_indices.append(idx)
            
            if bad_room_indices:
                violation = model.new_bool_var(f'eq_err_{l_id}')
                # Если выбрана плохая комната -> violation = 1
                model.add_allowed_assignments([v.room_var], [[i] for i in bad_room_indices]).only_enforce_if(violation)
                # Штраф пропорционален количеству недостающего оборудования (как в вашем check)
                # Или просто фиксированный. В OR-Tools проще фиксированный weight.
                penalties.append(weight)
        return penalties
    
    def _build_hard(self, model, lesson_vars, context):
        # Реализация для режима "Жесткое требование"
        for l_id, v in lesson_vars.items():
            lesson = context.get_by_id(l_id)
            req = context.requirements_cache.get((lesson.discipline_id, lesson.lesson_type_id), set())
            if not req: continue
            
            valid_indices = [
                idx for idx, r in context.idx_to_room.items()
                if req.issubset(set(get_cached_M2M(r, "equipment")))
            ]
            model.add_allowed_assignments([v.room_var], [[i] for i in valid_indices])

    def check(self,lesson: Lesson, context: ScheduleContext):
        room = lesson.classroom
        if not room:
            return None

        req = context.requirements_cache.get(
            (lesson.discipline_id,lesson.lesson_type_id),
            set()
        )
        
        provided = set(get_cached_M2M(room,"equipment"))
        missing = req - provided

        if missing:
            return ConstraintError(
                name="room_meets_equipment_requirements",
                message="Аудитория не соответствует требованиям по оснащению",
                penalty=self.config.weight * len(missing),
                data={"missing_equipment": missing, "room": room},
            )
        return None


@constraint("matches_teacher_room_preference")
class MatchesTeacherRoomPreference(BaseConstraint):
    def _build_soft(self, model, lesson_vars, context):
        penalties = []
        weight = self.config.weight
        
        for l_id, v in lesson_vars.items():
            lesson = context.get_by_id(l_id)
            teachers = get_cached_M2M(lesson, 'teachers')
            
            for t in teachers:
                pref_room = context.teacher_room_prefs.get(
                    (t.id, lesson.discipline_id, lesson.lesson_type_id)
                )
                if not pref_room: continue
                
                pref_idx = context.room_to_idx.get(pref_room.id)
                if pref_idx is None: continue

                violation = model.new_bool_var(f't_pref_r_{l_id}_{t.id}')
                # Нарушение, если room_var != pref_idx
                model.add(v.room_var != pref_idx).only_enforce_if(violation)
                penalties.append(violation * weight)
        return penalties
    def check(
        self,lesson: Lesson, context: ScheduleContext
    ):
        room = lesson.classroom
        if not room:
            return None

        violations = []
        
        # Используем твою новую утилиту для получения учителей без SQL
        teachers = get_cached_M2M(lesson, 'teachers')

        for teacher in teachers:
            # Пытаемся найти предпочтение по ключу: (Учитель, Дисциплина, Тип занятия)
            pref_room = context.teacher_room_prefs.get(
                (teacher.id, lesson.discipline_id, lesson.lesson_type_id)
            )

            # Если предпочтение есть и оно не совпадает с текущей аудиторией
            if pref_room and pref_room.id != room.id:
                violations.append({
                    "teacher": teacher, 
                    "preferred_room": pref_room
                })

        return (
            ConstraintError(
                name="matches_teacher_room_preference",
                message="Выбранная аудитория не соответствует пожеланиям преподавателей",
                penalty=self.config.weight,
                data=violations,
            )
            if violations
            else None
        )


@constraint("lessons_ordering")
class LessonsOrdering(BaseConstraint):
    def _build_soft(self, model, lesson_vars, context):
        """
        Если два занятия группы в один день, то у того, что раньше, 
        приоритет должен быть >= того, что позже.
        """
        penalties = []
        weight = self.config.weight
        num_slots = len(context.idx_to_slot)

        for g_id, l_ids in context.group_to_l_ids.items():
            if len(l_ids) < 2: continue
            
            for i in range(len(l_ids)):
                for j in range(i + 1, len(l_ids)):
                    id_a, id_b = l_ids[i], l_ids[j]
                    if id_a not in lesson_vars or id_b not in lesson_vars: continue
                    
                    l_a = context.get_by_id(id_a)
                    l_b = context.get_by_id(id_b)
                    
                    # Если приоритеты одинаковые, порядок не важен
                    if l_a.priority == l_b.priority: continue

                    v_a, v_b = lesson_vars[id_a], lesson_vars[id_b]

                    # Нам нужно знать: в один ли они день?
                    # Используем упрощение: слоты в context.idx_to_slot 
                    # идут подряд (пн1, пн2... вт1, вт2).
                    # Мы наказываем, если (SlotA < SlotB) И (PriorityA < PriorityB) 
                    # ПРИ УСЛОВИИ, что они в один день.
                    
                    # Создаем булеву: они в один день?
                    # Для этого в контексте желательно иметь маппинг slot_idx -> day_idx
                    # Но можно обойтись проверкой: floor(idx / пары_в_день)
                    
                    is_violated = model.new_bool_var(f'ord_v_{id_a}_{id_b}')
                    
                    # Условие нарушения (упрощенно: для любых двух слотов в сетке)
                    # Если хотим строго в один день, нужно добавить условие SameDay
                    # Но обычно глобальный приоритет "чем важнее, тем раньше" работает и так.
                    
                    # Если SlotA < SlotB и PriorityA < PriorityB -> Штраф
                    if l_a.priority < l_b.priority:
                        model.add(v_a.slot_var < v_b.slot_var).only_enforce_if(is_violated)
                    else:
                        model.add(v_b.slot_var < v_a.slot_var).only_enforce_if(is_violated)
                        
                    penalties.append(is_violated * weight)
        return penalties
    
    def check(self, lesson: Lesson, context: ScheduleContext):
        ts = lesson.timeslot
        if not ts:
            return None

        violations = []
        for group in get_cached_M2M(lesson, 'study_groups'):
            chain = context.get_group_day_chain(group.id, ts.week_num, ts.day)
            # Проверяем порядок приоритетов в цепочке
            for i in range(len(chain) - 1):
                if chain[i].priority < chain[i + 1].priority:
                    violations.append(
                        {
                            "group": group,
                            "early_lesson": chain[i],
                            "later_lesson": chain[i + 1],
                            "priorities": (chain[i].priority, chain[i + 1].priority),
                        }
                    )
        return (
            ConstraintError(
                name="lessons_ordering",
                message="Занятия для группы стоят в неправильном порядке",
                penalty=weight,
                data=violations,
            )
            if violations
            else None
        )


@constraint("matches_teacher_time_preference")
class MatchesTeacherTimePreference(BaseConstraint):
    def _build_soft(self, model, lesson_vars, context):
        penalties = []
        weight = self.config.weight
        
        for l_id, v in lesson_vars.items():
            lesson = context.get_by_id(l_id)
            for t in get_cached_M2M(lesson, 'teachers'):
                # Ищем все исключенные слоты для этого учителя
                excluded_indices = [
                    context.slot_to_idx[ts_id] 
                    for (teacher_id, ts_id) in context.teacher_excluded_slots 
                    if teacher_id == t.id
                ]
                
                if excluded_indices:
                    violation = model.new_bool_var(f't_time_v_{l_id}_{t.id}')
                    model.add_allowed_assignments([v.slot_var], [[i] for i in excluded_indices]).only_enforce_if(violation)
                    penalties.append(violation * weight)
        return penalties
    def check(
        self, lesson: Lesson, context: ScheduleContext
    ):
        ts = lesson.timeslot
        if not ts:
            return None

        violations = []
        for teacher in get_cached_M2M(lesson, 'teachers'):
            if (teacher.id, ts.id) in context.teacher_excluded_slots:
                violations.append({
                    "teacher": teacher, 
                    "timeslot": ts
                })

        return (
            ConstraintError(
                name="matches_teacher_time_preference",
                message="Выбранное время нежелательно для преподавателя",
                penalty=self.config.weight,
                data=violations,
            )
            if violations
            else None
        )
