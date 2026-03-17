# Отвечает за расчет хуегости расписания
from ..models.models import Lesson, BuildingPriority, Constraint, Timeslot

def calculate_penalty(scenario):
    """
    Считает итоговый штраф (вес) для конкретного сценария расписания.
    Чем меньше число, тем лучше расписание.
    """
    penalty = 0
    lessons = Lesson.objects.filter(scenario=scenario).select_related(
        'classroom__building', 'timeslot', 'academic_load'
    ).prefetch_related('study_groups')

    # Загружаем веса из таблицы Constraint (из нашей БД)
    # Если записей нет, используем дефолтные значения
    weights = {c.name: c.weight for c in Constraint.objects.all()}
    gap_weight = weights.get('window_gap', 100)
    building_switch_weight = weights.get('building_change', 500)

    #  Проверка ПРИОРИТЕТА КОРПУСОВ
    for lesson in lessons:
        building = lesson.classroom.building
        # Берем первый институт (предполагаем, что группы из одного института)
        group = lesson.study_groups.first()
        if group:
            institute = group.stud_program.institute
            # Ищем вес в BuildingPriority
            priority = BuildingPriority.objects.filter(institute=institute, building=building).first()
            if priority:
                penalty += priority.weight
            else:
                # Если здание не в приоритете и не родное - это огромный штраф
                penalty += 1000 

    # . Проверка ОКОН (разрывов) у групп 
    from django.db.models import Count
    all_groups = scenario.lessons.values_list('study_groups', flat=True).distinct()
    
    for group_id in all_groups:
        # Получаем все занятия группы в этот день, отсортированные по порядку
        group_lessons = lessons.filter(study_groups__id=group_id).order_by('timeslot__day', 'timeslot__order_number')
        
        last_lesson = None
        for current_lesson in group_lessons:
            if last_lesson and last_lesson.timeslot.day == current_lesson.timeslot.day:
                # Если разница между номерами пар больше 1 - это окно
                diff = current_lesson.timeslot.order_number - last_lesson.timeslot.order_number
                if diff > 1:
                    penalty += (diff - 1) * gap_weight
                
                #  Смена корпуса в течение дня 
                if last_lesson.classroom.building != current_lesson.classroom.building:
                    penalty += building_switch_weight
            
            last_lesson = current_lesson

    return penalty