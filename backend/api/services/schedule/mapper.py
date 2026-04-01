from collections import defaultdict
from typing import Any, List
from dataclasses import dataclass
from django.db.models import Q

from api.models import (
    Semester,
    ScheduleScenario,
    Lesson,
    ScheduleAdjustment,
    Booking,
    enums,
)
from datetime import datetime, timedelta, timezone

@dataclass
from api.models.constraints import AcademicLoad
class MappedEvent:
    event: Lesson | ScheduleAdjustment | Booking
    type: str
    date_start: datetime
    date_end: datetime


def get_semester_by_date(
    current_date: datetime = datetime.now(timezone.utc),
) -> Semester:
    """Ищем текущий семестр"""
    Semester.objects.filter().first()
    return Semester.objects.filter(
        date_start__lte=current_date,
        date_end__gte=current_date,
    ).first()


def get_active_scenario(sem) -> ScheduleScenario:
    """Ищем активный сценарий расписания на текущий семестр"""
    return ScheduleScenario.objects.filter(semester__id=sem.id, is_active=True).first()


def get_dates_qs(date_from: datetime, date_to: datetime) -> tuple[defaultdict[Any, List], Q]:
    # Собираем комбинации из таймслотов и да, попутно создаем фильтры для занятий
    lesson_dates = defaultdict(list)
    ts_filter = Q()

    seen = set()
    current_date = date_from
    while current_date <= date_to:
        # Номер дня в неделе
        day_of_week = current_date.weekday() + 1
        # Четность недели
        current_week_num = 1 if current_date.isocalendar()[1] % 2 != 0 else 2

        combo = (day_of_week, current_week_num)
        lesson_dates[combo].append(current_date)

        if combo not in seen:
            seen.add(combo)
            ts_filter |= Q(
                timeslot__day=day_of_week, timeslot__week_num=current_week_num
            )

        current_date += timedelta(days=1)

    return lesson_dates, ts_filter


def map_lessons(
    *, date_from: datetime, date_to: datetime, lessons = None
) -> List[MappedEvent]:
    #
    sem = get_semester_by_date(date_from)
    if not sem:
        raise ValueError("Не найден семестр для указанного промежутка дат")

    scenario = get_active_scenario(sem=sem)
    if not scenario:
        raise ValueError("Не найден активный сценарий в семестре")

    if not lessons:
        lessons = Lesson.objects
    lessons = (lessons.filter(scenario__id=scenario.id)
        .select_related("discipline", "lesson_type", "timeslot", "classroom")
        .prefetch_related("teachers", "study_groups"))

    lesson_dates, ts_filter = get_dates_qs(date_from, date_to)

    lessons = lessons.filter(ts_filter)
    lesson_ids = lessons.values_list("id", flat=True)

    adjustments = ScheduleAdjustment.objects.filter(
        status=enums.RequestStatus.VERIFIED,
        lesson__id__in=lesson_ids,
        date__gte=date_from,
        date__lte=date_to,
    ).select_related("lesson", "lesson__timeslot")

    mapped_events: List[MappedEvent] = [] 

    for lesson in lessons:
        # Берем корректировки для занятия
        lesson_adj = [a for a in adjustments if a.lesson.id == lesson.id]
        g_ids = lesson.study_groups.values_list("id",flat=True)
        t_ids = lesson.teachers.values_list("id",flat=True)
        # Для вывода обычных занятий мы контролируем количество академических часов.
        # Если в одном занятии участвуют несколько преподавателей и групп, то учебный план (AcademicLoad) совпадает!!!!!!!!.
        # Поэтому другие ограничения не учитываются - берется первая найденная запись
        load  = AcademicLoad.objects.filter(
            semester__id = sem.id,
            discipline__id = lesson.discipline.id,
            lesson_type__id = lesson.lesson_type.id,
            teacher__id__in = t_ids,
            study_group__id__in=g_ids
        ).first()
        if load:
            allowed_count = load.whole_hours // 2
            produced_count = 0

        # Получаем даты для слота
        dates = lesson_dates.get((lesson.timeslot.day, lesson.timeslot.week_num), [])

        for d in dates:
            # Находим корректировку на текущую дату
            day_adj = [a for a in lesson_adj if a.date == d]
            if day_adj:
                # Берем последнюю по created_at
                latest_adj = max(day_adj, key=lambda x: x.created_at)
                if latest_adj.timeslot:
                    mapped_events.append(
                        MappedEvent(
                            event=latest_adj,
                            type="adjustment",
                            date_start=datetime.combine(
                                d, latest_adj.lesson.timeslot.time_start
                            ),
                            date_end=datetime.combine(
                                d, latest_adj.lesson.timeslot.time_end
                            ),
                        )
                    )
            else:
                # Нет корректировки — берем обычное занятие
                if allowed_count is not None:
                    if produced_count >= allowed_count:
                        # Не выдаем занятие если превысили план
                        continue
                produced_count += 1            
                mapped_events.append(
                    MappedEvent(
                        event=lesson,
                        type="lesson",
                        date_start=datetime.combine(d, lesson.timeslot.time_start),
                        date_end=datetime.combine(d, lesson.timeslot.time_end),
                    )
                )

    return mapped_events

def map_bookings(*,date_from: datetime, date_to: datetime, classroom_id:int) -> List[MappedEvent]:
    bookings = Booking.objects.filter(
        status=enums.RequestStatus.VERIFIED,
        classroom__id=classroom_id,
        date_start__gte=date_from,
        date_start__lte=date_to,
    )
    return [MappedEvent(
        event=b,
        type="booking",
        date_start=b.date_start,
        date_end=b.date_end
    ) for b in bookings]

def get_group_schedule(*,group_id:int,date_from: datetime, date_to: datetime) -> List[MappedEvent]:
    lessons_qs = Lesson.objects.filter(
        groups__id__in=group_id
    )
    return map_lessons(date_from=date_from, date_to=date_to,lessons=lessons_qs)

def get_teacher_schedule(*,teacher_id:int,date_from: datetime, date_to: datetime) -> List[MappedEvent]:
    lessons_qs = Lesson.objects.filter(
        teachers__id__in=teacher_id
    )
    return map_lessons(date_from=date_from, date_to=date_to,lessons=lessons_qs)

def get_classroom_schedule(*,classroom_id:int,date_from: datetime, date_to: datetime) -> List[MappedEvent]:
    lessons_qs = Lesson.objects.filter(
        classroom__id=classroom_id
    )
    bookings = map_bookings(date_from=date_from,date_to=date_to,classroom_id=classroom_id)
    lessons = map_lessons(date_from=date_from, date_to=date_to,lessons=lessons_qs)
    return lessons.extend(bookings)