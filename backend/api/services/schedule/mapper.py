from collections import defaultdict
from typing import List
from django.db.models import Q, BaseManager

from api.models import (
    Semester,
    ScheduleScenario,
    Lesson,
    ScheduleAdjustment,
    Booking,
    enums,
)
from datetime import datetime, timedelta, timezone


class MappedEvent:
    event: Lesson | ScheduleAdjustment | Booking
    type: str
    date_start: datetime
    date_end: datetime


def get_semester_by_date(
    current_date: datetime = datetime.now(timezone.utc),
) -> Semester:
    """Ищем текущий семестр"""
    return Semester.objects.filter(
        date_start__lte=current_date,
        date_end__gte=current_date,
    ).first()


def get_active_scenario(sem) -> ScheduleScenario:
    """Ищем активный сценарий расписания на текущий семестр"""
    return ScheduleScenario.objects.filter(semester__id=sem.id, is_active=True).first()


def get_dates_qs(date_from: datetime, date_to: datetime):
    # Собираем комбинации из таймслотов и да, попутно создаем фильтры для занятий
    lesson_dates = defaultdict(List)
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
    *, date_from: datetime, date_to: datetime, lessons: BaseManager[Lesson] = None
) -> List[MappedEvent]:
    #
    sem = get_semester_by_date(date_from)
    if not sem:
        raise ValueError(detail="Не найден семестр для указанного промежутка дат")

    scenario = get_active_scenario(sem=sem)
    if not scenario:
        raise ValueError(detail="Не найден активный сценарий в семестре")

    if not lessons:
        lessons = Lesson.objects
    lessons = lessons.filter(scenario__id=scenario.id)

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

        # Получаем даты для слота
        dates = lesson_dates.get((lesson.timeslot.day, lesson.timeslot.week_num), [])

        for d in dates:
            # Находим корректировку на текущую дату
            day_adj = [a for a in lesson_adj if a.date == d]
            if day_adj:
                # Берем последнюю по created_at
                latest_adj = max(day_adj, key=lambda x: x.created_at)
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
                mapped_events.append(
                    MappedEvent(
                        event=lesson,
                        type="lesson",
                        date_start=datetime.combine(d, lesson.timeslot.time_start),
                        date_end=datetime.combine(d, lesson.timeslot.time_end),
                    )
                )

    return mapped_events
