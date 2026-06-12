from collections import defaultdict
import logging
import random
from types import SimpleNamespace
from typing import List, Dict
from django.db import transaction
from ortools.sat.python import cp_model

from api.models import *
from api.models import enums
from api.services.schedule.context import ScheduleContext
from api.services.constraints.manager import ConstraintManager

logger = logging.getLogger("generator")

class ORToolsTimetableGenerator:
    def __init__(self, scenario_id: int):
        self.scenario_id = scenario_id
        self.scenario = ScheduleScenario.objects.get(id=scenario_id)
        self.all_rooms = list(Classroom.objects.filter(allow_lessons=True).prefetch_related("building"))

        self._pref_cache = self._load_teacher_preferences()
        self._building_priority_cache = self._load_building_priorities()
        # 1. Гидратация: Превращаем PlannedLesson в список объектов Lesson (в RAM)
        self.in_memory_lessons = self._hydrate()
        
        # 2. Создаем контекст, передавая ему уже созданные объекты
        # generator=True заставит контекст построить индексы 0..N для Solver
        self.context = ScheduleContext(
            scenario_id=scenario_id, 
            lessons=self.in_memory_lessons, 
            generator=True
        )
        
        self.constraint_manager = ConstraintManager()
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        self.vars = {}
    def _load_teacher_preferences(self):
        """Кэш: (teacher_id, discipline_id, lesson_type_id) -> list[classroom_id]"""
        prefs = ClassroomPreference.objects.filter(status=enums.RequestStatus.VERIFIED)
        cache = defaultdict(list)
        for p in prefs:
            cache[(p.teacher_id, p.discipline_id, p.lesson_type_id)].append(p.classroom_id)
        return cache

    def _load_building_priorities(self):
        """Кэш: (institute_id, building_id) -> weight"""
        priorities = BuildingPriority.objects.all()
        cache = {}
        for p in priorities:
            cache[(p.institute_id, p.building_id)] = p.weight
        return cache
    def _get_suitable_rooms(self, pl: PlannedLesson) -> List[Classroom]:
        """Фильтр комнат по вместимости (базовое жесткое ограничение)"""
        # 1. Базовый фильтр по вместимости
        total_students = sum(g.students_count for g in pl.study_groups.all())
        base_rooms = [r for r in self.all_rooms if r.capacity >= total_students]
        
        if not base_rooms:
            return self.all_rooms

        # 2. Проверка предпочтений преподавателей (Жесткий фильтр)
        teachers = list(pl.teachers.all())
        pref_room_ids = set()
        
        # Собираем все комнаты, которые хотят учителя, учитывая их вес
        # Сортируем учителей по их весу (кто важнее, того комнату ищем первой)
        sorted_teachers = sorted(teachers, key=lambda t: t.constraint_weight, reverse=True)
        
        for t in sorted_teachers:
            room_ids = self._pref_cache.get((t.id, pl.discipline_id, pl.lesson_type_id), [])
            for rid in room_ids:
                pref_room_ids.add(rid)
        
        if pref_room_ids:
            # Если есть предпочтения, возвращаем ТОЛЬКО их (пересечение с вместимостью)
            suitable = [r for r in base_rooms if r.id in pref_room_ids]
            if suitable:
                return suitable

        # 3. Приоритет по институтам (Мягкое ранжирование)
        # Берем институт первой группы (обычно в одном PlannedLesson группы одного института)
        first_group = pl.study_groups.all()[0]
        institute_id = first_group.study_program.institute_id
        
        def get_room_rank(room):
            # Чем выше вес в BuildingPriority, тем меньше должен быть ранг (ближе к началу списка)
            # Если приоритет не задан, даем средний штрафной балл
            weight = self._building_priority_cache.get((institute_id, room.building_id), 0)
            return -weight # Инвертируем, чтобы больший вес был первым

        # Сортируем все подходящие по вместимости комнаты по весу корпусов
        # Дополнительно сортируем по названию корпуса, чтобы была группировка
        return sorted(base_rooms, key=lambda r: (get_room_rank(r), r.building.short_name))

    def _hydrate(self) -> List[Lesson]:
        """Создание объектов Lesson в памяти (аналогично вашему старому генератору)"""
        logger.info("Гидратация плановых занятий...")
        planned_items = list(PlannedLesson.objects.filter(
            semester=self.scenario.semester
        ).prefetch_related('teachers', 'study_groups', 'discipline', 'lesson_type'))
        
        
        fake_id_counter = -1
        lessons = []
        
        for pl in planned_items:
            suitable_rooms = self._get_suitable_rooms(pl)
            # print(len(suitable_rooms))
            teachers_list = list(pl.teachers.all())
            groups_list = list(pl.study_groups.all())

            for _ in range(pl.lessons_in_cycle):
                # Создаем объект без сохранения в БД
                lesson = Lesson(
                    id=fake_id_counter, # Отрицательный ID для идентификации в RAM
                    scenario=self.scenario,
                    discipline=pl.discipline,
                    lesson_type=pl.lesson_type,
                    whole_weeks=pl.whole_weeks,
                    priority=pl.priority,
                )
                # Имитируем кэш prefetch_related для работы ConstraintManager
                lesson._prefetched_objects_cache = {
                    'teachers': teachers_list,
                    'study_groups': groups_list
                }
                # Сохраняем список подходящих комнат прямо в объект для сборщика переменных
                lesson.suitable_room_ids = [r.id for r in suitable_rooms]
                
                lessons.append(lesson)
                fake_id_counter -= 1
        logger.info("Создано %s объектов Lesson...",len(lessons))
        return lessons

    def _create_variables(self):
        """Создание переменных решения"""
        num_slots = len(self.context.idx_to_slot)
        
        # self.vars будет словарем: { lesson_id: SimpleNamespace(slot_var, room_var) }
        self.vars = {} 

        for lesson in self.context.lessons:
            # 1. Создаем переменную для слота (0..N)
            slot_var = self.model.new_int_var(0, num_slots - 1, f'l_{lesson.id}_slot')

            # 2. Создаем переменную для аудитории (сразу ограничиваем домен)
            # Вспоминаем, что мы сохранили подходящие ID в гидраторе
            suitable_indices = [
                self.context.room_to_idx[rid] 
                for rid in lesson.suitable_room_ids if rid in self.context.room_to_idx
            ]
            
            room_var = self.model.new_int_var_from_domain(
                cp_model.Domain.from_values(suitable_indices), 
                f'l_{lesson.id}_room'
            )

            # 3. Сохраняем как объект, чтобы в ограничениях писать .slot_var
            self.vars[lesson.id] = SimpleNamespace(
                slot_var=slot_var,
                room_var=room_var
            )
            
        logger.info(f"Создано переменных для {len(self.vars)} занятий")

    def solve(self, time_limit=300):
        self._create_variables()
        
        # Применяем правила (пересечения учителей и т.д.)
        self.constraint_manager.apply_to_solver(
            model=self.model,
            lesson_vars=self.vars,
            context=self.context
        )
        
        self.solver.parameters.max_time_in_seconds = time_limit
        status = self.solver.solve(self.model)
        
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            self._update_objects_from_solution()
            return True
        return False

    def _update_objects_from_solution(self):
        """Записываем результаты решателя в объекты Lesson в памяти"""
        for lesson in self.context.lessons:
            res = self.vars[lesson.id]
            slot_idx = self.solver.value(res.slot_var)
            room_idx = self.solver.value(res.room_var)
            
            lesson.timeslot = self.context.idx_to_slot[slot_idx]
            lesson.classroom = self.context.idx_to_room[room_idx]

    @transaction.atomic
    def commit(self):
        """Финальное сохранение в БД с созданием M2M связей"""
        # Удаляем старое расписание этого сценария
        Lesson.objects.filter(scenario_id=self.scenario_id).delete()
        
        # Сбрасываем фейковые ID перед вставкой
        for l in self.in_memory_lessons:
            l.id = None
            l.pk = None
            
        # 1. Bulk create основных записей
        created_lessons = Lesson.objects.bulk_create(self.in_memory_lessons)
        
        # 2. Bulk create связей M2M (учителя и группы)
        TeacherThrough = Lesson.teachers.through
        GroupThrough = Lesson.study_groups.through
        
        t_links = []
        g_links = []
        
        for i, l in enumerate(created_lessons):
            # Берем данные из нашего RAM-объекта (порядковые номера совпадают)
            orig_lesson = self.in_memory_lessons[i]
            teachers = orig_lesson._prefetched_objects_cache['teachers']
            groups = orig_lesson._prefetched_objects_cache['study_groups']
            
            for t in teachers:
                t_links.append(TeacherThrough(lesson_id=l.id, teacher_id=t.id))
            for g in groups:
                g_links.append(GroupThrough(lesson_id=l.id, studygroup_id=g.id))
                
        TeacherThrough.objects.bulk_create(t_links)
        GroupThrough.objects.bulk_create(g_links)