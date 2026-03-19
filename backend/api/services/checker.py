#  проверка конфликтов для ручного редактирования и генерации будет тут
def check_lesson_conflicts(scenario, timeslot, classroom, teacher, study_group):
    """
    Возвращает список конфликтов для конкретного места в расписании.
    Если список пуст - ставить пару можно.
    """
    conflicts = []
    
    # Проверка: занята ли аудитория в это время в этом сценарии
    from ..models.models import Lesson
    if Lesson.objects.filter(scenario=scenario, timeslot=timeslot, classroom=classroom).exists():
        conflicts.append("Аудитория уже занята")

    # Проверка: занят ли преподаватель
    if Lesson.objects.filter(scenario=scenario, timeslot=timeslot, teachers=teacher).exists():
        conflicts.append(f"Преподаватель {teacher.name} уже ведет другую пару")

    # Проверка: занята ли группа
    if Lesson.objects.filter(scenario=scenario, timeslot=timeslot, study_groups=study_group).exists():
        conflicts.append(f"Группа {study_group.name} уже на занятии")

    return conflicts