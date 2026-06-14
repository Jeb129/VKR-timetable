import logging
from types import SimpleNamespace
from typing import List
from django.db import transaction
from ortools.sat.python import cp_model
from django.core.cache import cache

from api.models import *

from api.services.schedule.context import ScheduleContext
from api.services.constraints import ConstraintManager

logger = logging.getLogger("generator")

class StopSentinel(cp_model.CpSolverSolutionCallback):
    """
    Коллбэк для мониторинга внешних сигналов остановки.
    Вызывается OR-Tools при нахождении каждого промежуточного решения.
    """
    def __init__(self, scenario_id: int):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.scenario_id = scenario_id
        # Тот самый ключ, который мы определили в GenerationTaskManager
        self._meta_key = f"gen_meta_{scenario_id}"

    def on_solution_callback(self):
        """Метод, вызываемый решателем"""
        # Проверяем флаг остановки в Redis через метаданные задачи
        meta = cache.get(self._meta_key)
        
        if meta and meta.get("stop_signal") is True:
            logger.info(f"Получен сигнал остановки для сценария {self.scenario_id}. Прерываем поиск...")
            # Команда решателю немедленно прекратить работу
            self.StopSearch()

class ORToolsTimetableGenerator:
    """Обертка над ORtools SAT"""
    def __init__(self, scenario_id:int, context: ScheduleContext,constraint_manager: ConstraintManager):
        self.scenario_id = scenario_id
        self.context = context
        self.constraint_manager = constraint_manager
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        self.vars = {}


    def _create_variables(self):
        """Создание переменных решения"""
        num_slots = len(self.context.idx_to_slot)
        
        # self.vars будет словарем: { lesson_id: SimpleNamespace(slot_var, room_var) }
        self.vars = {} 

        for lesson in self.context.lessons:
            # 1. Создаем переменную для слота (0..N)
            slot_var = self.model.new_int_var(0, num_slots - 1, f'l_{lesson.id}_slot')

            suitable_indices = [
                self.context.room_to_idx[rid] 
                for rid in lesson.suitable_room_ids if rid in self.context.room_to_idx
            ]
            
            room_var = self.model.new_int_var_from_domain(
                cp_model.Domain.from_values(suitable_indices), 
                f'l_{lesson.id}_room'
            )

            self.vars[lesson.id] = SimpleNamespace(
                slot_var=slot_var,
                room_var=room_var
            )
            
        logger.info(f"Создано переменных для {len(self.vars)} занятий")

    def solve(self,time_limit=300, num_workers=8, log_progress=True):
        self._create_variables()
        
        self.constraint_manager.apply_to_solver(
            model=self.model,
            lesson_vars=self.vars,
            context=self.context
        )
        
        # Настройка параметров решателя
        self.solver.parameters.max_time_in_seconds = time_limit
        self.solver.parameters.num_search_workers = num_workers
        self.solver.parameters.log_search_progress = log_progress
        
        sentinel = StopSentinel(self.scenario_id)

        status = self.solver.solve(self.model,sentinel)
        
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
        self.context.rebuild_indexes()

class ScheduleGenerator:
    """Класс, предоставляющий сервис генерации расписания занятий"""
    # Подготавливает контекст занятий для отправки в решатель
    def __init__(self, scenario_id: int, constraints: List[Constraint] = None):
        self.scenario = ScheduleScenario.objects.get(id=scenario_id)
        self.all_rooms = list(Classroom.objects.filter(allow_lessons=True).prefetch_related("building"))
        self.context = ScheduleContext(scenario_id,generator=True,lessons=self._hydrate())
        self.constraint_manager = ConstraintManager(constraints)
        self.solver = ORToolsTimetableGenerator(
            scenario_id=self.scenario.id,
            context=self.context,
            constraint_manager=self.constraint_manager
        )
        self.solve = self.solver.solve

    def _hydrate(self):
        planned_items = list(PlannedLesson.objects.filter(
            semester=self.scenario.semester
        ).prefetch_related('teachers', 'study_groups', 'discipline', 'lesson_type'))


        fake_id_counter = -1
        lessons = []
        
        for pl in planned_items:
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
                lesson._prefetched_objects_cache = {
                    'teachers': teachers_list,
                    'study_groups': groups_list
                }
                lesson.suitable_room_ids = [r.id for r in self.all_rooms]
                
                lessons.append(lesson)
                fake_id_counter -= 1
        logger.info("Создано %s объектов Lesson...",len(lessons))
        return lessons
    
    
    @transaction.atomic
    def commit(self):
        """Сохранение результата генерации в БД"""
        # Удаляем старое расписание этого сценария
        Lesson.objects.filter(scenario_id=self.scenario.id).delete()
        
        # Сбрасываем фейковые ID перед вставкой
        for l in self.context.lessons:
            l.id = None
            l.pk = None
            
        # 1. Bulk create основных записей
        created_lessons = Lesson.objects.bulk_create(self.context.lessons)
        
        # 2. Bulk create связей M2M (учителя и группы)
        TeacherThrough = Lesson.teachers.through
        GroupThrough = Lesson.study_groups.through
        
        t_links = []
        g_links = []
        
        for i, l in enumerate(created_lessons):
            # Берем данные из нашего RAM-объекта (порядковые номера совпадают)
            orig_lesson = self.context.lessons[i]
            teachers = orig_lesson._prefetched_objects_cache['teachers']
            groups = orig_lesson._prefetched_objects_cache['study_groups']
            
            for t in teachers:
                t_links.append(TeacherThrough(lesson_id=l.id, teacher_id=t.id))
            for g in groups:
                g_links.append(GroupThrough(lesson_id=l.id, studygroup_id=g.id))
                
        TeacherThrough.objects.bulk_create(t_links)
        GroupThrough.objects.bulk_create(g_links)