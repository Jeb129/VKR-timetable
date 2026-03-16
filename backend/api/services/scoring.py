# Отвечает за расчет хуегости расписания

def calculate_scenario_penalty(scenario):
    total_penalty = 0
    lessons = scenario.lessons.all().select_related(
        'classroom__building', 
        'timeslot'
    ).prefetch_related('study_groups__stud_program__institute')

    # Ограничение из таблицы Constraint (например, "Окно в расписании")
    gap_penalty_weight = Constraint.objects.get(name="window_gap").weight 
    
    for group in StudyGroup.objects.all():
        group_lessons = lessons.filter(study_groups=group).order_by('timeslot__day', 'timeslot__time_start')
        
        # Логика поиска окон и штрафов за них
        
        
    # Логика BuildingPriority (Приоритет корпуса для института)
    for lesson in lessons:
        building = lesson.classroom.building
        # Берем институт первой группы в занятии
        institute = lesson.study_groups.first().stud_program.institute
        
        # Ищем, какой приоритет у этого здания для этого института
        priority = BuildingPriority.objects.filter(institute=institute, building=building).first()
        
        if priority:
            # Если в приоритете weight высокий — это плохо (штраф)
            total_penalty += priority.weight
        else:
            # Если связи вообще нет — это огромный штраф (чужой корпус)
            total_penalty += 5000 

    return total_penalty