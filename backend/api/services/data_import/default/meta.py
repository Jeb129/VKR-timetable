from api.models import *


def init_lesson_types():
    lt_count = 0
    lesson_types = [
        ("Лекция", "Лек", False, True, True),
        ("Практическое занятие", "Пр", True, True, False),
        ("Лабораторная работа", "Лаб", False, False, False),
    ]
    for (
        name,
        short_name,
        allow_merge_teachers,
        allow_merge_subgroups,
        allow_merge_groups,
    ) in lesson_types:
        _, created = LessonType.objects.get_or_create(
            name=name,  # name теперь уникальное поле
            short_name=short_name,
            allow_merge_teachers=allow_merge_teachers,
            allow_merge_subgroups=allow_merge_subgroups,
            allow_merge_groups=allow_merge_groups,
        )
        if created:
            lt_count += 1
    return f"Создано {lt_count} видов занятимй"


def init_timeslots():
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
        for day in range(1, 7):
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
    return f"Создано {ts_count} слотов расписания"


def init_semesters():
    sems = [
        ("Осень 2019", "2019-09-01", "2019-12-31"),
        ("Весна 2020", "2020-02-01", "2020-06-30"),
        ("Осень 2020", "2020-09-01", "2020-12-31"),
        ("Весна 2021", "2021-02-01", "2021-06-30"),
        ("Осень 2021", "2021-09-01", "2021-12-31"),
        ("Весна 2022", "2022-02-01", "2022-06-30"),
        ("Осень 2022", "2022-09-01", "2022-12-31"),
        ("Весна 2023", "2023-02-01", "2023-06-30"),
        ("Осень 2023", "2023-09-01", "2023-12-31"),
        ("Весна 2024", "2024-02-01", "2024-06-30"),
        ("Осень 2024", "2024-09-01", "2024-12-31"),
        ("Весна 2025", "2025-02-01", "2025-06-30"),
        ("Осень 2025", "2025-09-01", "2025-12-31"),
        ("Весна 2026", "2026-02-01", "2026-06-30"),
        ("Осень 2026", "2026-09-01", "2026-12-31"),
        ("Весна 2027", "2027-02-01", "2027-06-30"),
    ]
    s_count = 0
    for n, s, e in sems:
        _, created = Semester.objects.get_or_create(name=n, date_start=s, date_end=e)
        if created:
            s_count += 1
    return f"Создано {s_count} семестров"
