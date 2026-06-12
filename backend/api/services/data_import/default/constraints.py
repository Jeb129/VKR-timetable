from api.models import *


def init_building_priorities():
    """
    Первоначальное заполнение приоритетов корпусов для институтов
    на основе статистики проведенных занятий.
    Вес (weight): 100 - максимально предпочтительно, 1 - нежелательно.
    """
    # Данные в формате: (Код Института, Код Корпуса, Вес/Приоритет)
    priorities_data = [
        # ИВИТШ
        ("ИВИТШ", "Б", 85),
        ("ИВИТШ", "Гл", 9),
        
        # ИГНИСТ
        ("ИГНИСТ", "В1", 89),
        ("ИГНИСТ", "Б1", 11),
        
        # ИКИ
        ("ИКИ", "Ж", 100),
        
        # ИПП
        ("ИПП", "ИПП", 100),
        
        # ИПТД
        ("ИПТД", "Гл", 38),
        ("ИПТД", "Ж", 19),
        ("ИПТД", "Е", 11),
        ("ИПТД", "Б", 7),
        
        # ИУЭФ
        ("ИУЭФ", "В1", 58),
        ("ИУЭФ", "Гл", 36),
        ("ИУЭФ", "Б1", 6),
        
        # ИФМЕН
        ("ИФМЕН", "Е", 100),
        
        # ЮИН
        ("ЮИН", "Г1", 70),  
        ("ЮИН", "В1", 17),
        ("ЮИН", "Б1", 13),
    ]

    created_count = 0
    updated_count = 0
    errors = []

    for inst_sn, bld_sn, weight in priorities_data:
        try:
            # Ищем институт и корпус. Если не находим - пропускаем эту запись
            institute = Institute.objects.get(short_name=inst_sn)
            building = Building.objects.get(short_name=bld_sn)

            # Создаем или обновляем приоритет
            obj, created = BuildingPriority.objects.update_or_create(
                institute=institute,
                building=building,
                defaults={"weight": weight}
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        except Institute.DoesNotExist:
            errors.append(f"Институт '{inst_sn}' не найден в базе")
        except Building.DoesNotExist:
            errors.append(f"Корпус '{bld_sn}' не найден в базе")
        except Exception as e:
            errors.append(f"Ошибка при обработке {inst_sn}-{bld_sn}: {str(e)}")

    # Вывод результата (для логов или консоли)
    result_msg = (
        f"Завершено. Создано: {created_count}, Обновлено: {updated_count}. "
        f"Ошибок: {len(errors)}"
    )   
    return result_msg


def init_travel_times():
    # Список разрешенных переходов: (Корпус 1, Корпус 2, время в пути в минутах)
    travel_data = [
            # Дзержинского / Ивановская
            ("Б","Гл",10),

            # 1 Мая
            ("Б1","В1",10),
            ("В1","Г1",10),
            ("Г1","Б1",10),

            # Главный / 1 мая
            ("Б1","Гл",30),
            ("В1","Гл",10),
            ("Г1","Гл",10),
            ("Ж","Гл",30)
        ]

    buildings = {b.short_name: b for b in Building.objects.all()}
    created_count = 0

    for sn1, sn2, minutes in travel_data:
        b1 = buildings.get(sn1)
        b2 = buildings.get(sn2)

        if b1 and b2:
            # Создаем запись в обе стороны
            # А -> Б
            BuildingTravelTime.objects.update_or_create(
                from_building=b1,
                to_building=b2,
                defaults={"travel_time_minutes": minutes}
            )
            # Б -> А
            BuildingTravelTime.objects.update_or_create(
                from_building=b2,
                to_building=b1,
                defaults={"travel_time_minutes": minutes}
            )
            created_count += 2
        else:
            missing = sn1 if not b1 else sn2
            print(f"Пропущено: корпус {missing} не найден в БД")

    return f"Заполнено {created_count} записей времени переходов."


def init_constraints():
    constraints = [
        # --- КРИТИЧЕСКИЕ (HARD) ---
        ("Пересечение по преподавателю", 500, "teacher_no_overlap",True,False,False),
        ("Пересечение по группе", 500, "group_no_overlap",True,False,False),
        ("Пересечение по аудиториям", 500, "room_no_overlap",True,False,False),
        ("Аудитория вмещает всех студентов", 500, "room_has_enough_seats",True,False,False),
        ("Физическая невозможность перехода между корпусами", 500, "building_travel_impossible",True,False,False),

        # --- ТЕХНИЧЕСКИЕ И ПРИОРЕТЕТНЫЕ ---
        ("Аудитория соответствует оборудованию", 400, "room_meets_equipment_requirements",False,False,False),
        ("Предпочтения преподавателя по аудитории", 300, "matches_teacher_room_preference",False,False,False),
        ("Ручной приоритет расположения занятий", 300, "lessons_ordering",False,False,True),
        ("Предпочтения преподавателя по времени", 200, "matches_teacher_time_preference",False,False,False),

        # --- ЭРГОНОМИКА (КАЧЕСТВО РАСПИСАНИЯ) ---
        ("Дневная перегрузка группы",150,"group_daily_overload",False,False,False),
        ("Дневная перегрузка преподавателя",100,"teacher_daily_overload",False,False,False),
        ("Превышение недельной нагрузки преподавателя", 50, "teacher_weekly_overload",False,False,False),
        ("Превышение недельной нагрузки группы", 50, "group_weekly_overload",False,False,False),
        ("Окно у студентов", 100, "students_gap",False,False,False),
        ("Окно у преподавателя", 50, "teachers_gap",False,False,False),
        ("Факт смены корпуса в течение дня", 100, "building_clustering",False,False,False),
        ("Занятия с малым количеством часов не должны стоять в середине дня", 100, "lesson_persistence_sort",False,False,False),
        ("Приоритет заполнения первой половины дня", 80, "morning_preference",False,False,True),

    ]

    c_count = 0
    for description, weight, name, is_hard, exlude_generation, exclude_manual in constraints:
        _, created = Constraint.objects.get_or_create(
            name=name,  # name теперь уникальное поле
            defaults={
                "weight": weight, 
                "description": description,
                "is_hard":is_hard,
                "manual_only":exlude_generation,
                "generation_only":exclude_manual},
        )
        if created:
            c_count += 1
    
    return f"Создано {c_count} ограничений"
        
