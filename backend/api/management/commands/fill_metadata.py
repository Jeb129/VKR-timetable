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
        
        # Заполняем базовые веса для ограничений (Constraints)
        constraints = [
            ("window_gap", 100),       # Окно у студентов
            ("building_change", 500),  # Смена корпуса между парами
            ("teacher_overload", 50),  # Слишком много пар у препода подряд
        ]
        for name, weight in constraints:
            Constraint.objects.get_or_create(name=name, weight=weight)

        self.stdout.write(self.style.SUCCESS('Сетка времени и базовые веса созданы!'))