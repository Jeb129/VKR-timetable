from collections import defaultdict
import random
import time
import logging
import math
from typing import List
from django.db import transaction
from api.models import enums, PlannedLesson, Lesson, Timeslot, Classroom, ScheduleScenario,ClassroomPreference, BuildingPriority
from api.services.constraints import ConstraintManager
from api.services.schedule.context import ScheduleContext

logger = logging.getLogger("generator")

class TimetableGenerator:
    def __init__(self, scenario_id: int):
        self.scenario_id = scenario_id
        self.scenario = ScheduleScenario.objects.get(id=scenario_id)
        self.all_slots = list(Timeslot.objects.all())
        self.all_rooms = list(Classroom.objects.filter(is_virtual=False).prefetch_related("building","equipment"))
        
        # Кэшируем справочники для ускорения _hydrate
        self._pref_cache = self._load_teacher_preferences()
        self._building_priority_cache = self._load_building_priorities()

        self.constraint_manager = ConstraintManager()
        self.context = None

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
        """Создание объектов в RAM"""
        logger.info("Загрузка информации о запланированных занятиях сценария...")
        planned_items = list(PlannedLesson.objects.filter(semester=self.scenario.semester).prefetch_related(
            'teachers', 'study_groups', 'discipline', 'lesson_type'
        ))
        logger.info(f"Найдено {len(planned_items)} запланированных занятий для семестра {self.scenario.semester}")
        logger.info("Предварительная генерация и индексация занятий")

        fake_id_counter = -1
        in_memory_lessons = []
        for pl in planned_items:
            suitable_rooms = self._get_suitable_rooms(pl)
            teachers_list = list(pl.teachers.all())
            groups_list = list(pl.study_groups.all())

            for _ in range(pl.lessons_in_cycle):
                lesson = Lesson(
                    id = fake_id_counter,
                    scenario=self.scenario,
                    discipline=pl.discipline,
                    lesson_type=pl.lesson_type,
                    whole_weeks=pl.whole_weeks,
                    priority=pl.priority,
                    timeslot=random.choice(self.all_slots),
                    classroom=suitable_rooms[0]
                )
                lesson._prefetched_objects_cache = {
                    'teachers': teachers_list,
                    'study_groups': groups_list
                }
                # Сохраняем данные для быстрой проверки ограничений и работы генератора
                lesson.suitable_rooms = suitable_rooms
                lesson.total_students = sum(g.students_count for g in lesson.study_groups.all())

                in_memory_lessons.append(lesson)
                fake_id_counter -= 1
        logger.info(f"Сгенерировано и {len(in_memory_lessons)} занятий")
        return in_memory_lessons

    def _get_total_penalty(self, lessons: List[Lesson]) -> int:
            """
            Двухэтапная оценка: 
            1. Сначала считаем только Hard Constraints (Level 2).
            2. Если они есть — возвращаем их сумму, умноженную на большой коэффициент.
            3. Если Hard = 0 — считаем Soft Constraints (Level 1).
            """
            hard_penalty = 0
            # 1-й проход: ищем только критические ошибки
            # print(f"Проверка {len(lessons)} занятий")
            for l in lessons:
                # Передаем constraint_level=2 (только Hard)
                # print(f"Проверка {l.id} Жесткие ограничения")

                h_errors = self.constraint_manager.check(
                    lesson=l, 
                    context=self.context, 
                    constraint_level=2,
                    generation_only=True
                )
                if h_errors:
                    hard_penalty += sum(err.penalty for err in h_errors)
            
            # Если есть хотя бы одна жесткая ошибка, мягкие даже не проверяем!
            if hard_penalty > 0:
                # Возвращаем "огромный" штраф, чтобы отжиг стремился сначала убрать его
                return hard_penalty * 1_000_000 

            # 2-й проход: если всё легально, начинаем бороться за удобство (Level 1)
            soft_penalty = 0
            for l in lessons:
                # print(f"Проверка {l.id} Мягкие ограничения")
                s_errors = self.constraint_manager.check(
                    lesson=l, 
                    context=self.context, 
                    constraint_level=1,
                    generation_only=True
                )
                soft_penalty += sum(err.penalty for err in s_errors)
                
            return soft_penalty

    def run(self, iterations: int = 10000, t_start: float = 100.0, cooling_rate: float = 0.9995):
        """
        Параметры
        :iterations: общее кол-во шагов
        :t_start: начальная температура (чем выше, тем больше хаоса в начале)
        :cooling_rate: скорость остывания (0.99 - быстро, 0.9999 - медленно)
        """
        
        # 1. Инициализация
        lessons = self._hydrate()
        self.context = ScheduleContext(scenario_id=self.scenario_id, lessons=lessons)
        
        # current_penalty = 1000
        current_penalty = self._get_total_penalty(lessons)
        best_penalty = current_penalty
        temp = t_start
        
        logger.info(f"Начало генерации. Штраф: {current_penalty}, Температура: {temp}")
        start = time.time()
        for i in range(iterations):
            # 2. Выбор случайного занятия
            logger.debug(f"Итерация {i+1} из {iterations}")
            lesson = random.choice(lessons)
            
            old_slot, old_room = lesson.timeslot, lesson.classroom
            
            # 3. Мутация
            new_slot = random.choice(self.all_slots)
            new_room = random.choice(lesson.suitable_rooms)
            
            # 4. Применение мутации к индексам контекста
            self.context.update_lesson_location(lesson, new_slot, new_room)
            
            # 5. Оценка
            new_penalty = self._get_total_penalty(lessons)
            delta = new_penalty - current_penalty
            
            # 6. Решение о принятии шага
            accept = False
            if delta <= 0:
                # Стало лучше или так же — принимаем всегда
                accept = True
            else:
                # Стало хуже — принимаем с вероятностью по формуле Больцмана
                probability = math.exp(-delta / temp)
                if random.random() < probability:
                    accept = True
            
            if accept:
                current_penalty = new_penalty
                # Если это лучшее, что мы видели за всё время — запоминаем
                if current_penalty < best_penalty:
                    best_penalty = current_penalty
            else:
                # Откат
                self.context.update_lesson_location(lesson, old_slot, old_room)

            # 7. Остывание
            temp *= cooling_rate
            
            if i % 1000 == 0:
                logger.info(f"Итерация {i}: Штраф={current_penalty}, T={temp:.2f}")
            
            if current_penalty == 0:
                logger.info("Найдено идеальное расписание!")
                break
        end = time.time() - start
        logger.info(f"Генерация завершена. Итоговый штраф: {current_penalty} Затраченное время: {end} сек.")
        return lessons,current_penalty

    @transaction.atomic
    def commit(self, lessons: List[Lesson]):
        """Сохранение в БД (как в предыдущем примере)"""
        Lesson.objects.filter(scenario_id=self.scenario_id).delete()
        # Подготавливаем объекты к вставке
        for l in lessons:
            l.pk = None  # Сбрасываем наш временный отрицательный ID
            l.id = None

        created_lessons = Lesson.objects.bulk_create(lessons)
        
        LessonTeacher = Lesson.teachers.through
        LessonGroup = Lesson.study_groups.through
        
        teachers_links = []
        groups_links = []
        
        for i, l in enumerate(created_lessons):
            orig = lessons[i]
            for t in orig._prefetched_objects_cache['teachers']:
                teachers_links.append(LessonTeacher(lesson_id=l.id, teacher_id=t.id))
            for g in orig._prefetched_objects_cache['study_groups']:
                groups_links.append(LessonGroup(lesson_id=l.id, studygroup_id=g.id))
        
        LessonTeacher.objects.bulk_create(teachers_links)
        LessonGroup.objects.bulk_create(groups_links)