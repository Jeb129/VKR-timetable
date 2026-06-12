from rest_framework.views import APIView
from rest_framework.response import Response
from api.models import Building, Classroom, Lesson, Timeslot, Booking
from django.shortcuts import get_object_or_404
from datetime import datetime

class BuildingLoadView(APIView):
    def get(self, request):
        building_id = request.query_params.get('building_id')
        classroom_id = request.query_params.get('classroom_id')
        
        unique_slots_count = Timeslot.objects.values('day', 'order_number', 'week_num').distinct().count()
        max_hours_cycle = unique_slots_count * 1.5

        MAX_PAIRS_PER_DAY = 7

        # РЕЖИМ 3: Детальная информация по конкретной аудитории (для модалки)
        if classroom_id:
            room = get_object_or_404(Classroom, id=classroom_id)
            daily_stats = {1: {d: 0 for d in range(1, 7)}, 2: {d: 0 for d in range(1, 7)}}
            lessons = Lesson.objects.filter(classroom=room, scenario__is_active=True).select_related('timeslot')
            for l in lessons:
                daily_stats[l.timeslot.week_num][l.timeslot.day] += 1

            active_bookings = Booking.objects.filter(classroom=room, status=1, date_start__gte=datetime.now())
            
            return Response({
                "num": room.num,
                "daily_load": daily_stats,
                "max_pairs": 7,
                "booking_count": active_bookings.count(), # Добавили счетчик
                "bookings": [{
                    "date": b.date_start.strftime("%d.%m"),
                    "time": f"{b.date_start.strftime('%H:%M')} - {b.date_end.strftime('%H:%M')}",
                    "reason": b.description,
                } for b in active_bookings]
            })

        # РЕЖИМ 1: Список аудиторий корпуса
        if building_id:
            building = get_object_or_404(Building, id=building_id)
            classroom_stats = []
            for room in building.classrooms.all():
                actual_lessons = Lesson.objects.filter(classroom=room, scenario__is_active=True).count()
                actual_hours = actual_lessons * 1.5
                load_percent = round((actual_hours / max_hours_cycle) * 100, 1)

                classroom_stats.append({
                    "id": room.id,
                    "num": room.num,
                    "load_percent": load_percent,
                    "actual_hours": actual_hours, 
                    "max_hours": max_hours_cycle   
                })
            return Response({"building_name": building.name, "classrooms": classroom_stats})

        # РЕЖИМ 2: Общая статистика по корпусам
        buildings_stats = []
        for b in Building.objects.all():
            rooms = b.classrooms.all()
            if rooms.count() == 0: continue
            
            actual_lessons = Lesson.objects.filter(classroom__building=b, scenario__is_active=True).count()
            actual_hours = actual_lessons * 1.5
            total_max_hours = rooms.count() * max_hours_cycle
            load_percent = round((actual_hours / total_max_hours) * 100, 1)

            buildings_stats.append({
                "id": b.id,
                "short_name": b.short_name,
                "load_percent": load_percent,
                "rooms_count": rooms.count(),
                "lessons_count": actual_lessons 
            })
        return Response(buildings_stats)