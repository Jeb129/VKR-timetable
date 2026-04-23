from django.core.management.base import BaseCommand

# ИСПРАВЛЕННЫЕ ИМПОРТЫ: вытягиваем модели из новых файлов
from api.models import *


class Command(BaseCommand):
    help = "Заполнение сетки времени и базовых ограничений"

    def handle(self, *args, **kwargs):
        # 1. Заполняем сетку времени (6 дней по 7 пар)
        days = range(1, 7)  # Пн-Сб
        pairs = [
            ("08:30", "10:00"),
            ("10:10", "11:40"),
            ("11:50", "13:20"),
            ("14:00", "15:30"),
            ("15:40", "17:10"),
            ("17:20", "18:50"),
            ("19:00", "20:30"),
        ]

        ts_count = 0
        for week in [1, 2]:  # Числитель и знаменатель
            for day in days:
                for idx, (start, end) in enumerate(pairs, 1):
                    # Используем get_or_create, чтобы не дублировать при повторном запуске
                    _, created = Timeslot.objects.get_or_create(
                        day=day,
                        week_num=week,
                        order_number=idx,
                        defaults={"time_start": start, "time_end": end},
                    )
                    if created:
                        ts_count += 1
        sems = [
            ("Осень 2019","2019-09-01","2019-12-31"),
            ("Весна 2020","2020-02-01","2020-06-30"),
            ("Осень 2020","2020-09-01","2020-12-31"),
            ("Весна 2021","2021-02-01","2021-06-30"),
            ("Осень 2021","2021-09-01","2021-12-31"),
            ("Весна 2022","2022-02-01","2022-06-30"),
            ("Осень 2022","2022-09-01","2022-12-31"),
            ("Весна 2023","2023-02-01","2023-06-30"),
            ("Осень 2023","2023-09-01","2023-12-31"),
            ("Весна 2024","2024-02-01","2024-06-30"),
            ("Осень 2024","2024-09-01","2024-12-31"),
            ("Весна 2025","2025-02-01","2025-06-30"),
            ("Осень 2025","2025-09-01","2025-12-31"),
            ("Весна 2026","2026-02-01","2026-06-30"),
            ("Осень 2026","2026-09-01","2026-12-31"),
            ("Весна 2027","2027-02-01","2027-06-30"), 
        ]
        s_count = 0
        for (n,s,e) in sems:
            _, created = Semester.objects.get_or_create(
                name=n,
                date_start=s,
                date_end=e
            )
            if created:
                s_count += 1
        
        institutes = [
            ("Институт педагогики и психологии","ИПП"),
            ("Иститут гуманитарных наук и социальных технологий", "ИГНИСТ"),
            ("Институт Высшая ИТ-школа", "ИВИТШ"),
            ("Институт физико-математических и естественных наук", "ИФМЕН"),
            ("Юридический институт имени А. Некрасова", "ЮИН"),
            ("Институт промышленных технологий и дизайна", "ИПТД"),
            ("Институт управления экономики и финаснсов", "ИУЭФ"),
            ("Институт культуры и искусств", "ИКИ")
        ]
        i_count = 0
        for (n, sn) in institutes:
            _, created = Institute.objects.get_or_create(
                name=n,
                short_name=sn
            )
            if created:
                i_count += 1
        # 2. Заполняем ограничения (Constraints)
        # Формат: (Описание, Вес, Техническое имя)
        constraints = [
            ("Пересечение по преподавателю", 500, "teacher_no_overlap"),
            ("Пересечение по группе", 500, "group_no_overlap"),
            ("Пересечение по аудиториям", 500, "room_no_overlap"),
            ("Аудитория вмещает всех студентов", 500, "room_has_enough_seats"),
            (
                "Аудитория соответствует оборудованию",
                400,
                "room_meets_equipment_requirements",
            ),
            (
                "Предпочтения преподавателя по аудитории",
                300,
                "matches_teacher_room_preference",
            ),
            (
                "Предпочтения преподавателя по времени",
                200,
                "matches_teacher_time_preference",
            ),
            ("Переход между корпусами", 500, "building_change"),
            ("Окно у студентов", 100, "students_gap"),
            ("Окно у преподавателя", 50, "teachers_gap"),
            ("Перегрузка преподавателя", 50, "teacher_overload"),
        ]

        c_count = 0
        for description, weight, name in constraints:
            _, created = Constraint.objects.get_or_create(
                name=name,  # name теперь уникальное поле
                defaults={"weight": weight, "description": description},
            )
            if created:
                c_count += 1

        lt_count = 0
        lesson_types = [
            ("Лекция","Лек",False,True,True),
            ("Практическое занятие","Пр",True,True,False),
            ("Лабораторная работа","Лаб",False,False,False)

        ]
        for name, short_name,allow_merge_teachers,allow_merge_subgroups,allow_merge_groups in lesson_types:
            _, created = LessonType.objects.get_or_create(
                name=name,  # name теперь уникальное поле
                short_name=short_name,
                allow_merge_teachers=allow_merge_teachers,
                allow_merge_subgroups=allow_merge_subgroups,
                allow_merge_groups=allow_merge_groups
            )
            if created:
                lt_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Создано: \n" +
                f"{ts_count} таймслотов!\n" +
                f"{s_count} семестров\n" +
                f"{i_count} институтов\n" +
                f"{c_count} ограничений!\n" +
                f"{lt_count} типов занятий!\n"

            )
        )
