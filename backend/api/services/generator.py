# расставляем нагрузку и ищем ей самое дешевое место

from ..models.models import Lesson, AcademicLoad, Timeslot, Classroom, ScheduleScenario
from .scoring import calculate_penalty
from .checker import check_lesson_conflicts 

def run_simple_generator(scenario_name="Авто-генерация"):
    # 1. Создаем новый сценарий
    scenario = ScheduleScenario.objects.create(name=scenario_name)
    
    # 2. Берем всю учебную нагрузку
    loads = AcademicLoad.objects.all()
    
    # 3. Берем все доступные слоты и аудитории
    timeslots = Timeslot.objects.all().order_by('day', 'order_number')
    classrooms = Classroom.objects.all()

    for load in loads:
        # Для каждого часа в нагрузке (например, 2 пары в неделю)
        for _ in range(load.hours_per_week):
            placed = False
            best_slot = None
            best_room = None
            min_added_penalty = float('inf')

            # Ищем свободное место
            for slot in timeslots:
                for room in classrooms:
                    # Проверяем жесткие конфликты (занятость препода/аудитории/группы)
                    conflicts = check_lesson_conflicts(scenario, slot, room, load.teacher, load.study_group)
                    
                    if not conflicts:
                        # Вместимость аудитории
                        if room.capacity < load.study_group.students_count:
                            continue

                        # Временно создаем занятие, чтобы оценить "вес"
                        test_lesson = Lesson.objects.create(
                            scenario=scenario,
                            discipline=load.discipline,
                            lesson_type=load.lesson_type,
                            timeslot=slot,
                            classroom=room,
                            academic_load=load
                        )
                        test_lesson.teachers.add(load.teacher)
                        test_lesson.study_groups.add(load.study_group)

                        # Считаем, насколько увеличился штраф
                        current_penalty = calculate_penalty(scenario)
                        
                        if current_penalty < min_added_penalty:
                            min_added_penalty = current_penalty
                            best_slot = slot
                            best_room = room
                        
                        # Удаляем тестовое занятие
                        test_lesson.delete()
                        placed = True
                        break # Для простоты берем первый подошедший вариант или лучший
                if placed: break

            # Финально закрепляем лучшее найденное место
            if best_slot and best_room:
                final_lesson = Lesson.objects.create(
                    scenario=scenario,
                    discipline=load.discipline,
                    lesson_type=load.lesson_type,
                    timeslot=best_slot,
                    classroom=best_room,
                    academic_load=load
                )
                final_lesson.teachers.add(load.teacher)
                final_lesson.study_groups.add(load.study_group)

    # Сохраняем итоговый штраф в сценарий
    scenario.total_penalty = calculate_penalty(scenario)
    scenario.save()
    return scenario