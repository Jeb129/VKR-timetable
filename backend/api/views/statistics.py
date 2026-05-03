from rest_framework.views import APIView
from rest_framework.response import Response
from api.models import Building, Classroom, Lesson, Timeslot, Booking
from django.shortcuts import get_object_or_404
from datetime import datetime

class BuildingLoadView(APIView):
    def get(self, request):
        building_id = request.query_params.get('building_id')
        classroom_id = request.query_params.get('classroom_id')
        
        # Считаем количество доступных часов за 2 недели
        total_slots_cycle = Timeslot.objects.count() # Всего слотов в БД 
        # Если в вузе 7 пар в день, 6 дней в неделю, 2 недели = 84 слота.
        slots_per_room = total_slots_cycle / (Classroom.objects.count() or 1) 
        unique_slots_count = Timeslot.objects.values('day', 'order_number', 'week_num').distinct().count()
        max_hours_cycle = unique_slots_count * 1.5

        # РЕЖИМ 3: Детальная информация по конкретной аудитории (для модалки)
        if classroom_id:
            room = get_object_or_404(Classroom, id=classroom_id)
            # Одобренные брони 
            active_bookings = Booking.objects.filter(
                classroom=room, 
                status=1, 
                date_start__gte=datetime.now()
            ).order_by('date_start')
            
            return Response({
                "num": room.num,
                "booking_count": active_bookings.count(),
                "bookings": [{
                    "date": b.date_start.strftime("%d.%m.%Y"),
                    "time": f"{b.date_start.strftime('%H:%M')} - {b.date_end.strftime('%H:%M')}",
                    "reason": b.description,
                    "user": b.user.username
                } for b in active_bookings]
            })

        # РЕЖИМ 1: Список аудиторий корпуса
        if building_id:
            building = get_object_or_404(Building, id=building_id)
            classrooms = building.classrooms.all()
            classroom_stats = []
            for room in classrooms:
                actual_lessons = Lesson.objects.filter(classroom=room, scenario__is_active=True).count()
                actual_hours = actual_lessons * 1.5
                load_percent = round((actual_hours / max_hours_cycle) * 100, 1) if max_hours_cycle > 0 else 0

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
            r_count = rooms.count()
            if r_count == 0: continue

            actual_lessons = Lesson.objects.filter(classroom__building=b, scenario__is_active=True).count()
            actual_hours = actual_lessons * 1.5
            total_max_hours = r_count * max_hours_cycle
            load_percent = round((actual_hours / total_max_hours) * 100, 1) if total_max_hours > 0 else 0

            buildings_stats.append({
                "id": b.id,
                "short_name": b.short_name,
                "load_percent": load_percent,
                "rooms_count": r_count,
                "total_hours": actual_hours
            })
        return Response(buildings_stats)