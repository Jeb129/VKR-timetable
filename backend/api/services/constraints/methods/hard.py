from api.services.constraints.meta import constraint, ConstraintError,BaseConstraint
from api.services.schedule.context import ScheduleContext
from api.models import Lesson
from config.utils import get_cached_M2M
from django.forms.models import model_to_dict



@constraint("teacher_no_overlap")
class TeacherNoOverlap(BaseConstraint):
    def _build_hard(self, model, lesson_vars, context):
        for entity_id, l_ids in context.teacher_to_l_ids.items(): # или group_to_l_ids
            if len(l_ids) < 2: continue
            
            intervals = []
            for l_id in l_ids:
                if l_id not in lesson_vars: continue
                
                v = lesson_vars[l_id]
                # Создаем интервал: начало=слот, длительность=1, конец=слот+1
                # Это ОДНА переменная вместо сотен попарных проверок
                suffix = f"t{entity_id}_l{l_id}"
                start = v.slot_var
                size = 1
                end = model.new_int_var(0, len(context.idx_to_slot), f"end_{suffix}")
                model.add(end == start + size)
                
                interval = model.new_interval_var(start, size, end, f"iv_{suffix}")
                intervals.append(interval)
            
            if intervals:
                # Магическая функция, которая работает в C++ и не ест память Python
                model.add_no_overlap(intervals)

    def check(self, lesson, context):
        ts_id = lesson.timeslot.id
        if not ts_id:
            return None

        violations = []
        for teacher in get_cached_M2M(lesson,"teachers"):
            others = context.teacher_lookup.get((teacher.id, ts_id), [])
            for other in others:
                if other.id != lesson.id:
                    violations.append({"teacher": teacher, "lesson": other})
        return (
            ConstraintError(
                name="teacher_no_overlap",
                message="Некоторые преподаватели заняты в это время",
                penalty=self.config.weight,
                data=violations[:10],
            )
            if violations
            else None
        )

@constraint("group_no_overlap")
class GroupNoOverlap(BaseConstraint):
    def _build_hard(self, model, lesson_vars, context):
        for entity_id, l_ids in context.group_to_l_ids.items(): # или group_to_l_ids
            if len(l_ids) < 2: continue
            
            intervals = []
            for l_id in l_ids:
                if l_id not in lesson_vars: continue
                
                v = lesson_vars[l_id]
                # Создаем интервал: начало=слот, длительность=1, конец=слот+1
                # Это ОДНА переменная вместо сотен попарных проверок
                suffix = f"g{entity_id}_l{l_id}"
                start = v.slot_var
                size = 1
                end = model.new_int_var(0, len(context.idx_to_slot), f"end_{suffix}")
                model.add(end == start + size)
                
                interval = model.new_interval_var(start, size, end, f"iv_{suffix}")
                intervals.append(interval)
            
            if intervals:
                # Магическая функция, которая работает в C++ и не ест память Python
                model.add_no_overlap(intervals)
                
    def check(self,lesson,context):
        ts_id = lesson.timeslot.id
        if not ts_id:
            return None

        violations = []
        for group in get_cached_M2M(lesson,"study_groups"):
            others = context.group_lookup.get((group.id, ts_id), [])
            for other in others:
                if other.id != lesson.id:
                    violations.append({"group": group, "lesson": other})
        return (
            ConstraintError(
                name="group_no_overlap",
                message="Некоторые группы заняты в это время",
                penalty=self.config.weight,
                data=violations[:10],
            )
            if violations
            else None
        )


@constraint("room_no_overlap")
class RoomNoOverlap(BaseConstraint):
    def _build_hard(self, model, lesson_vars, context):
        num_slots = len(context.idx_to_slot)
        num_rooms = len(context.idx_to_room)
        
        # Константа для смещения (чтобы виртуальные занятия не пересекались с реальными)
        # 300 комнат * 84 слота = 25 200. Сделаем запас.
        virtual_offset = (num_rooms * num_slots) + 1000
        
        # Подготовка карты физических комнат для add_element
        # 1 - обычная комната (нужен контроль), 0 - виртуальная/параллельная
        phys_map = [
            1 if (not r.is_virtual and not r.allow_parallel) else 0 
            for r in context.idx_to_room.values()
        ]

        presence_indices = []

        for l_id, v in lesson_vars.items():
            # 1. Определяем, является ли выбранная комната "физической"
            # Это стоит 1 BoolVar и 1 add_element на занятие
            is_phys = model.new_bool_var(f'is_phys_{l_id}')
            model.add_element(v.room_var, phys_map, is_phys)

            # 2. Вычисляем глобальный индекс ячейки (адрес)
            # Если физическая: addr = room_idx * num_slots + slot_idx
            # Если виртуальная: addr = virtual_offset + unique_id
            addr = model.new_int_var(0, virtual_offset + abs(l_id), f'addr_{l_id}')

            # Условие для физической комнаты
            model.add(addr == v.room_var * num_slots + v.slot_var).only_enforce_if(is_phys)
            
            # Условие для виртуальной комнаты (используем ID занятия как уникальный ключ)
            # l_id у нас отрицательный (-1, -2...), поэтому берем abs()
            model.add(addr == virtual_offset + abs(l_id)).only_enforce_if(is_phys.Not())
            
            presence_indices.append(addr)

        # 3. Одно ограничение AllDifferent на все занятия
        # Оно гарантирует, что ни у каких двух занятий в "физическом" режиме не совпадет адрес
        model.add_all_different(presence_indices)
        
    # def _build_hard(self, model, lesson_vars, context):
    #     num_slots = len(context.idx_to_slot)
    #     all_presence_vars = []

    #     for l_id, l_var in lesson_vars.items():
    #         # Линеаризация ячейки
    #         cell_idx = model.new_int_var(0, 2000000, f'cell_{l_id}')
    #         is_phys = model.new_bool_var(f'is_phys_{l_id}')
            
    #         phys_room_indices = [
    #             idx for idx, r in context.idx_to_room.items() 
    #             if not r.is_virtual and not r.allow_parallel
    #         ]
            
    #         # Связываем через разрешенные значения
    #         model.add_allowed_assignments([l_var.room_var], [[i] for i in phys_room_indices]).only_enforce_if(is_phys)
    #         model.add_forbidden_assignments([l_var.room_var], [[i] for i in phys_room_indices]).only_enforce_if(is_phys.not_negated())

    #         # Если физ. комната: cell_idx = room * total_slots + slot
    #         model.add(cell_idx == l_var.room_var * num_slots + l_var.slot_var).only_enforce_if(is_phys)
    #         # Если вирт: уникальный ID вне диапазона
    #         model.add(cell_idx == 2000000 - abs(l_id)).only_enforce_if(is_phys.not_negated())
            
    #         all_presence_vars.append(cell_idx)

    #     model.add_all_different(all_presence_vars)

    def check(self, lesson, context):
        ts = lesson.timeslot
        room = lesson.classroom
        
        if not ts or not room:
            return None
        if room.allow_parallel:
            return None

        others = [
            other
            for other in context.classroom_lookup.get((room.id, ts.id), [])
            if other.id != lesson.id
        ]
        if others:
            return ConstraintError(
                name="room_no_overlap",
                message=f"Аудитория {room} занята в это время",
                penalty=self.config.weight,
                data=[{"room": room, "lesson": other} for other in others[:10]],
            )
        return None
    


@constraint("room_has_enough_seats")
class RoomHasEnoughSeats(BaseConstraint):
    def _build_hard(self, model, lesson_vars, context):
        for l_id, l_var in lesson_vars.items():
            lesson = context.get_by_id(l_id)
            capacity_needed = getattr(lesson, 'total_students', None) or sum(g.students_count for g in get_cached_M2M(lesson, "study_groups"))
            
            valid_indices = [
                idx for idx, r in context.idx_to_room.items() 
                if r.capacity >= capacity_needed or r.is_virtual
            ]
            # Domain Reduction через разрешенные значения
            model.add_allowed_assignments([l_var.room_var], [[i] for i in valid_indices])

    def check(self, lesson, context):
        room = lesson.classroom
        if not room or room.is_virtual:
            return None

        total_students = getattr(lesson, 'total_students', None) or sum(g.students_count for g in lesson.study_groups.all())

        if total_students > room.capacity:
            return ConstraintError(
                name="room_has_enough_seats",
                penalty=self.config.weight,
                message=f"Требуется {total_students} мест, в наличии {room.capacity}",
                data={"required": total_students, "capacity": room.capacity, "room": room},
            )
        return None
    
# @constraint("building_travel_impossible")
class BuildingTravelImpossible(BaseConstraint):
    def _build_hard(self, model, lesson_vars, context):
        num_bldgs = len(context.building_to_idx)
        num_slots = len(context.slot_to_idx)

        # Объединяем всех, кто должен успевать перемещаться
        entities = list(context.teacher_to_l_ids.items()) + list(context.group_to_l_ids.items())

        for _, l_ids in entities:
            if len(l_ids) < 2: continue
            
            for i in range(len(l_ids)):
                for j in range(i + 1, len(l_ids)):
                    id_a, id_b = l_ids[i], l_ids[j]
                    if id_a not in lesson_vars or id_b not in lesson_vars: continue
                    
                    v_a, v_b = lesson_vars[id_a], lesson_vars[id_b]

                    # 1. Здания (через индексы OR-Tools)
                    b_idx_a = model.new_int_var(0, num_bldgs - 1, f'ba_{id_a}')
                    b_idx_b = model.new_int_var(0, num_bldgs - 1, f'bb_{id_b}')
                    model.add_element(v_a.room_var, context.room_building_indices, b_idx_a)
                    model.add_element(v_b.room_var, context.room_building_indices, b_idx_b)

                    # 2. Матрица перемещений (нужно b_idx_a * num_bldgs + b_idx_b)
                    travel_idx = model.new_int_var(0, num_bldgs * num_bldgs, f'tidx_{id_a}_{id_b}')
                    model.add(travel_idx == b_idx_a * num_bldgs + b_idx_b)
                    needed = model.new_int_var(0, 1440, f'need_{id_a}_{id_b}')
                    model.add_element(travel_idx, context.flat_travel_matrix, needed)

                    # 3. Матрица перерывов (нужно slot_idx_a * num_slots + slot_idx_b)
                    gap_idx = model.new_int_var(0, num_slots * num_slots, f'gidx_{id_a}_{id_b}')
                    model.add(gap_idx == v_a.slot_var * num_slots + v_b.slot_var)
                    avail = model.new_int_var(0, 1440, f'avail_{id_a}_{id_b}')
                    model.add_element(gap_idx, context.flat_gap_matrix, avail)

                    # Условие
                    model.add(avail >= needed)
    # def _build_hard(self, model, lesson_vars, context):
    #     num_bldgs = len(context.building_to_idx)
    #     num_slots = len(context.slot_to_idx)

    #     # Группируем по учителям и группам (кто перемещается)
    #     # Нам нужны только ID занятий
    #     entity_to_l_ids = {**context.teacher_to_l_ids, **context.group_to_l_ids}

    #     for ent_id, l_ids in entity_to_l_ids.items():
    #         if len(l_ids) < 2: continue
            
    #         for i in range(len(l_ids)):
    #             for j in range(i + 1, len(l_ids)):
    #                 id_a, id_b = l_ids[i], l_ids[j]
    #                 var_a, var_b = lesson_vars[id_a], lesson_vars[id_b]

    #                 # 1. Получаем ИНДЕКСЫ зданий для обоих занятий
    #                 b_idx_a = model.new_int_var(0, num_bldgs - 1, f'ba_{id_a}')
    #                 b_idx_b = model.new_int_var(0, num_bldgs - 1, f'bb_{id_b}')
    #                 model.add_element(var_a.room_var, context.room_building_indices, b_idx_a)
    #                 model.add_element(var_b.room_var, context.room_building_indices, b_idx_b)

    #                 # 2. Получаем необходимое время (Needed) из матрицы перемещений
    #                 travel_idx = model.new_int_var(0, num_bldgs * num_bldgs, f'tidx_{id_a}_{id_b}')
    #                 model.add(travel_idx == b_idx_a * num_bldgs + b_idx_b)
                    
    #                 needed_time = model.new_int_var(0, 1440, f'need_{id_a}_{id_b}')
    #                 model.add_element(travel_idx, context.flat_travel_matrix, needed_time)

    #                 # 3. Получаем доступное время (Available) из матрицы перерывов
    #                 gap_idx = model.new_int_var(0, num_slots * num_slots, f'gidx_{id_a}_{id_b}')
    #                 model.add(gap_idx == var_a.slot_var * num_slots + var_b.slot_var)
                    
    #                 available_time = model.new_int_var(0, 1440, f'avail_{id_a}_{id_b}')
    #                 model.add_element(gap_idx, context.flat_gap_matrix, available_time)

    #                 # 4. ФИНАЛЬНОЕ УСЛОВИЕ: Available >= Needed
    #                 model.add(available_time >= needed_time)

    def check(self, lesson, context):
        ts = lesson.timeslot
        room = lesson.classroom
        
        if not ts or not room or room.is_virtual:
            return None

        violations = []

        teachers = get_cached_M2M(lesson,"teachers")
        groups = get_cached_M2M(lesson,"study_groups")

        check_list = [("teacher", teachers), ("group", groups)]

        for type_name, entities in check_list:
            for ent in entities:
                # Получаем соседей из индекса контекста
                prev_l, next_l = (
                    context.get_teacher_neighbors(lesson, ent.id)
                    if type_name == "teacher"
                    else context.get_group_neighbors(lesson, ent.id)
                )

                # Проверяем и предыдущее, и следующее занятие
                if prev_l:
                    # Оцениваем перемещение с предыдущего на текущее
                    err = _check_travel(prev_l, lesson, context, "prev")
                    if err: violations.append({**err, "entity": ent, "type": type_name})
                
                if next_l:
                    # Оцениваем перемещение с текущего на следующее
                    err = _check_travel(lesson, next_l, context, "next")
                    if err: violations.append({**err, "entity": ent, "type": type_name})

        return (
            ConstraintError(
                name="building_travel_impossible",
                message="Недостаточно времени для перехода",
                penalty=self.config.weight,
                data=violations,
            )
            if violations
            else None
        )
    
def _check_travel(l1: Lesson, l2: Lesson, context: ScheduleContext, direction):
    """
    Вспомогательная функция для проверки пары занятий.
    Работает БЕЗ обращений к БД.
    """
    # Если аудитории нет или она виртуальная — перемещение всегда возможно
    r1, r2 = l1.classroom, l2.classroom
    if not r1 or not r2 or r1.is_virtual or r2.is_virtual:
        return None
    
    b1_id, b2_id = r1.building_id, r2.building_id
    if b1_id == b2_id:
        return None

    # Ищем время перемещения в кэше. Если нет в базе - считаем очень далеким (999)
    travel_min = context.travel_map.get((b1_id, b2_id), 999)
    
    # Берем время из кэша слотов
    _, t1_end = context.slot_times.get(l1.timeslot_id, (0,0))
    t2_start, _ = context.slot_times.get(l2.timeslot_id, (0,0))

    available = t2_start - t1_end
    
    if travel_min > available:
        return {
            "travel_time": travel_min,
            "available_time": available,
            "neighbor_lesson": l1 if direction == "prev" else l2,
        }
    return None