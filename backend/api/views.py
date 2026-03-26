# backend/api/views.py
from rest_framework import viewsets
from datetime import datetime
from .models.models import Lesson, Classroom
from .serializers.education import LessonSerializer
from .serializers.infrastructure import ClassroomSerializer

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

class ClassroomViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Classroom.objects.all().order_by('num')
    serializer_class = ClassroomSerializer