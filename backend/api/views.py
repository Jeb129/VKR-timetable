# backend/api/views.py
from rest_framework import viewsets
from rest_framework.response import Response
from datetime import datetime
from rest_framework.decorators import action
from .models.models import Lesson, Classroom, Booking
from django.utils.dateparse import parse_date
from .serializers.education import LessonSerializer
from .serializers.infrastructure import ClassroomSerializer
from .serializers.requests import BookingSerializer

class LessonViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

    def get_queryset(self):
        queryset = Lesson.objects.all().select_related(
            'discipline', 'lesson_type', 'timeslot', 'classroom'
        ).prefetch_related('teachers', 'study_groups')

        # Фильтрация по аудитории
        classroom_id = self.request.query_params.get('classroom_id')
        if classroom_id:
            queryset = queryset.filter(classroom_id=classroom_id)
        
        # фильтр по дате и четности
        date_str = self.request.query_params.get('date')
        if date_str:
            try:
                # Превращаем строку '2026-03-25' в объект даты
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                
                # А) День недели (Пн=1, Вс=7)
                day_of_week = dt.weekday() + 1
                
                # Б) Чётность недели (Числитель/Знаменатель)
                # В России обычно: Нечетная неделя года = Числитель (1), Четная = Знаменатель (2)
                # ISO-номер недели:
                week_number = dt.isocalendar()[1]
                # Если номер недели нечетный - ставим 1, если четный - 2
                current_week_num = 1 if week_number % 2 != 0 else 2
                
                print(f"\n--- ФИЛЬТРАЦИЯ ---")
                print(f"Дата: {date_str} | День недели: {day_of_week} | Неделя года: {week_number}")
                print(f"Определено как: {'ЧИСЛИТЕЛЬ' if current_week_num == 1 else 'ЗНАМЕНАТЕЛЬ'} (week_num={current_week_num})")
                print(f"------------------\n")
                
                # Применяем фильтры к базе
                queryset = queryset.filter(
                    timeslot__day=day_of_week, 
                    timeslot__week_num=current_week_num
                )
                
            except ValueError:
                pass # Если дата пришла в битом формате - отдаем как есть

        # Только активный сценарий (EIOS Import)
        queryset = queryset.filter(scenario__is_active=True)
        
        return queryset.order_by('timeslot__order_number')
    
    @action(detail=False, methods=['get'])
    def my(self, request):
        """Возвращает уроки текущего авторизованного пользователя"""
        user = request.user
        queryset = Lesson.objects.filter(scenario__is_active=True)

        # Если это преподаватель
        if hasattr(user, 'teacher'):
            queryset = queryset.filter(teachers=user.teacher)
        # Если это студент (нужно будет связать User и StudyGroup позже)
        # elif ... 

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

    @action(detail=False, methods=['get'])
    def busy_slots(self, request):
        room_id = request.query_params.get('classroom_id')
        date_str = request.query_params.get('date')
        
        if not room_id or not date_str:
            return Response([])

        target_date = parse_date(date_str)
        day_of_week = target_date.weekday() + 1
        
        # Считаем неделю года
        week_num_year = target_date.isocalendar()[1]
        # Чётность: 1 - нечетная (числитель), 2 - четная (знаменатель)
        calc_week_num = 1 if week_num_year % 2 != 0 else 2
        
        print(f"\n=== [LOG] ПРОВЕРКА ЗАНЯТОСТИ ===")
        print(f"Аудитория ID: {room_id}")
        print(f"Дата: {date_str} (День недели: {day_of_week})")
        print(f"Неделя года: {week_num_year} -> Очередь: {calc_week_num}")

        # Ищем занятия
        lessons = Lesson.objects.filter(
            classroom_id=room_id,
            timeslot__day=day_of_week,
            timeslot__week_num=calc_week_num,
            scenario__is_active=True
        ).select_related('timeslot', 'discipline')

        print(f"Найдено уроков в базе: {lessons.count()}")

        busy = []
        for l in lessons:
            start = l.timeslot.time_start.strftime("%H:%M")
            end = l.timeslot.time_end.strftime("%H:%M")
            busy.append({
                "start": start,
                "end": end,
                "title": l.discipline.name,
                "type": "lesson"
            })
            print(f" -> Занято: {start} - {end} ({l.discipline.name})")

        # Ищем брони
        bookings = Booking.objects.filter(
            classroom_id=room_id,
            date_start__date=target_date,
            status=1 # VERIFIED
        )
        print(f"Найдено одобренных броней: {bookings.count()}")
        for b in bookings:
            busy.append({
                "start": b.date_start.strftime("%H:%M"),
                "end": b.date_end.strftime("%H:%M"),
                "title": "Забронировано",
                "type": "booking"
            })

        print(f"=== [END LOG] ===\n")
        return Response(busy)

class ClassroomViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Classroom.objects.all().order_by('num')
    serializer_class = ClassroomSerializer