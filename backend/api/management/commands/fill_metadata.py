from django.core.management.base import BaseCommand
from api.models.models import Timeslot, Constraint

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        # Заполняем сетку времени (6 дней по 6 пар)
        days = range(1, 7)  # Пн-Сб
        pairs = [
            ("08:30", "10:00"),
            ("10:10", "11:40"),
            ("11:50", "13:20"),
            ("14:00", "15:30"),
            ("15:40", "17:10"),
            ("17:20", "18:50"),
        ]
        
        for week in [1, 2]: # Числитель и знаменатель
            for day in days:
                for idx, (start, end) in enumerate(pairs, 1):
                    Timeslot.objects.get_or_create(
                        day=day,
                        week_num=week,
                        order_number=idx,
                        time_start=start,
                        time_end=end
                    )

        constraints = [
            ("Пересечение по преподавателю", 500, "teacher_no_overlap"),
            ("Пересечение по группе", 500, "group_no_overlap"),
            ("Пересечение по аудиториям", 500, "room_no_overlap"),
            ("Аудитория вмещает всех студентов", 500, "room_has_enough_seats"),
            ("Аудитория соответствует оборудованию", 400, "room_meets_equipment_requirements"),
            ("Предпочтения преподавателя по аудитории", 300, "matches_teacher_room_preference"),
            ("Предпочтения преподавателя по времени", 200, "matches_teacher_time_preference"),
            ("Переход между корпусами", 500, "building_change"),
            ("Окно у студентов", 100, "students_gap"),
            ("Окно у преподавателя", 50, "teachers_gap"), # Тоже важно, оказывается, но парвда окно у препода побольше
            ("Перегрузка преподователя",50,"teacher_overload")
        ]
        for description, weight, name in constraints:
            Constraint.objects.get_or_create(name=name, weight=weight, description=description)

        self.stdout.write(self.style.SUCCESS('Сетка времени и базовые веса созданы!'))