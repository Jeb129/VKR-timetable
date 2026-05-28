import logging
from typing import Any, Dict, List
from dataclasses import dataclass
from django.forms.models import model_to_dict

from django.db.models import Q
from datetime import date, datetime, timedelta, timezone
from api.models import (
    Semester,
    ScheduleScenario,
    Lesson,
    ScheduleAdjustment,
    Booking,
    enums,
)

logger = logging.getLogger("schedule")
sql_logger = logging.getLogger("sql")


@dataclass
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


class ScheduleMapper:
    def __init__(self, date_from: datetime, date_to: datetime, 
                    scenario: ScheduleScenario = None,
                    classroom_id: int = None, 
                    teacher_id: int = None, 
                    group_id: int = None):
        
        self.date_from = date_from
        self.date_to = date_to

        self.classroom_id = classroom_id
        self.teacher_id = teacher_id
        self.group_id = group_id

        if scenario:
            self.scenario = scenario
            self.semester = scenario.semester
        else:
            self.semester = get_semester_by_date(date_from.date())
            if not self.semester:
                raise ValueError(f"Не найден семестр для даты {date_from.date()}")
            self.scenario = get_active_scenario(self.semester)
            if not self.scenario:
                raise ValueError(f"Не найден активный семестр для даты {date_from.date()}")

    def _get_week_parity(self, d: date) -> int:
        """Определяем четность по календарной неделе (1-нечет, 2-чет)"""
        return 1 if d.isocalendar()[1] % 2 != 0 else 2


    def _get_week_index(self, d: date) -> int:
        """Порядковый номер недели в семестре (1, 2, 3...)"""
        return d.isocalendar()[1] - self.semester.date_start.isocalendar()[1] + 1
    

    def _event_matches_filters(self, lesson: Lesson, current_classroom_id: int) -> bool:
        """
        Проверяет, соответствует ли событие (в его текущем состоянии) 
        запрошенным фильтрам (преподаватель, группа, аудитория).
        """
        # Фильтр по аудитории (самый динамичный)
        if self.classroom_id is not None and current_classroom_id != self.classroom_id:
            return False
        
        # Фильтр по преподавателю (состав не меняется корректировкой, смотрим исходное занятие)
        
        if self.teacher_id:
            if not any(t.id == self.teacher_id for t in lesson.teachers.all()):
                return False
                
        # Фильтр по группе
        if self.group_id:
            if not any(g.id == self.group_id for g in lesson.study_groups.all()):
                return False        
        return True
    

    def map_lessons(self) -> List[MappedEvent]:
        
        # Фильтрация занятий и корректировок
        lesson_q = Q(scenario_id = self.scenario.id)
        adjusment_q = Q()

        if self.classroom_id:
            lesson_q &= Q(classroom_id = self.classroom_id)
            adjusment_q = Q(classroom_id = self.classroom_id)
        elif self.teacher_id:
            lesson_q &= Q(teachers__id = self.teacher_id)
        elif self.group_id:
            lesson_q &= Q(study_groups__id = self.group_id)

        lessons_qs = Lesson.objects.filter(lesson_q)

        adjusment_q |= Q(lesson__in=lessons_qs)

        adjustments_qs = ScheduleAdjustment.objects.filter(
            adjusment_q,
            date__range=(self.date_from.date(), self.date_to.date()),
            request__status=enums.RequestStatus.VERIFIED
        ).select_related('timeslot', 'classroom', 'classroom__building', 'request')

        # sql_logger.info(lessons_qs.query)
        # sql_logger.info(adjustments_qs)

        grid_lesson_ids = set(lessons_qs.values_list('id', flat=True))
        # print("\nРезультат: ",grid_lesson_ids)
        adj_lesson_ids = set(adjustments_qs.values_list('lesson_id', flat=True))
        all_relevant_ids = grid_lesson_ids | adj_lesson_ids


        all_lessons = list(Lesson.objects.filter(id__in = all_relevant_ids)
                     .select_related(
                        'discipline', 'lesson_type', 'timeslot', 'classroom', 'classroom__building'
                    ).prefetch_related(
                        'teachers', 'study_groups'
                    )
                )
        
        lessons_lookup = {l.id: l for l in all_lessons}

        adj_map: Dict[Any,ScheduleAdjustment] = {}
        for a in adjustments_qs.order_by('request__created_at'):
            adj_map[(a.date, a.lesson_id)] = a

        result: List[MappedEvent] = []

        current_date = self.date_from.date()
        while current_date <= self.date_to.date():
            day_of_week = current_date.weekday() + 1
            parity = self._get_week_parity(current_date)
            week_idx = self._get_week_index(current_date)
            print(
                f"Проверка даты {str(current_date)}\n" 
                f"Четность: {parity}\n"
                f"Номер недели в семестре: {week_idx}"
                )

            # Собираем все события на этот день
            # Сначала проверяем корректировки (они могут добавить "чужие" занятия в этот день)
            for (adj_date, l_id), adj in adj_map.items():
                if adj_date == current_date and adj.timeslot:
                    lesson = lessons_lookup.get(l_id)
                    if self._event_matches_filters(lesson, adj.classroom_id):
                        result.append(MappedEvent(
                            event=adj,
                            type= enums.EventType.SCHEDULE_ADJUSTMENT,
                            date_start=datetime.combine(current_date,adj.timeslot.time_start),
                            date_end=datetime.combine(current_date,adj.timeslot.time_end)
                        ))

            # Теперь проверяем сетку
            adjusted_lesson_ids_today = {l_id for (d, l_id) in adj_map if d == current_date}
            
            for lesson in all_lessons:
                print(model_to_dict(lesson))
                # Если занятие сегодня по сетке
                if lesson.timeslot.day == day_of_week and lesson.timeslot.week_num == parity:
                    print("занятие сегодня по сетке")
                    # Если на него НЕТ корректировки сегодня
                    if lesson.id not in adjusted_lesson_ids_today:
                        print("на него НЕТ корректировки сегодня")
                        # Проверяем фильтры и длительность
                        print(
                                "фильтры и длительность\n"
                                f"{week_idx} <= {lesson.whole_weeks} = {week_idx <= lesson.whole_weeks}"
                                  )
                        if self._event_matches_filters(lesson, lesson.classroom_id):
                            if not lesson.whole_weeks or week_idx <= lesson.whole_weeks:
                                result.append(MappedEvent(
                                    event=lesson,
                                    type=enums.EventType.LESSON,
                                    date_start=datetime.combine(current_date,lesson.timeslot.time_start),
                                    date_end=datetime.combine(current_date,lesson.timeslot.time_end)
                                ))
            current_date += timedelta(days=1)
        print(
            f"Найдено занятий: {len(lessons_lookup)}",
            f"Корректировок: {len(adj_map)}",
            "результат:",
            result,
            sep="\n"
        )
        return result


    def map_bookings(self) -> List[MappedEvent]:
        bookings = Booking.objects.filter(
            status=enums.RequestStatus.VERIFIED,
            date_start__lt=self.date_to,
            date_end__gt=self.date_from,
        )

        if self.classroom_id:
            bookings = bookings.filter(
                classroom_id = self.classroom_id
            )

        return [
            MappedEvent(
                event=b,
                type=enums.EventType.BOOKING,
                date_start=b.date_start,
                date_end=b.date_end,
            )
            for b in bookings
        ]
    

    def get_schedule(self) -> List[MappedEvent]:
        result: List[MappedEvent] = []
        
        lessons = self.map_lessons()
        result.extend(lessons)

        bookings = self.map_bookings() if self.classroom_id else []
        result.extend(bookings)

        return result