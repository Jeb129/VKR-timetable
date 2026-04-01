from django.core.management.base import BaseCommand
# ИСПРАВЛЕННЫЕ ИМПОРТЫ: вытягиваем модели из новых файлов
from api.models.schedule import Timeslot
from api.models.constraints import Constraint

class Command(BaseCommand):
    help = 'Заполнение сетки времени и базовых ограничений'

    def handle(self, *args, **kwargs):
        # 1. Заполняем сетку времени (6 дней по 7 пар)
        days = range(1, 7)  # Пн-Сб
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
        for week in [1, 2]: # Числитель и знаменатель
            for day in days:
                for idx, (start, end) in enumerate(pairs, 1):
                    # Используем get_or_create, чтобы не дублировать при повторном запуске
                    obj, created = Timeslot.objects.get_or_create(
                        day=day,
                        week_num=week,
                        order_number=idx,
                        defaults={
                            'time_start': start,
                            'time_end': end
                        }
                    )
                    if created: ts_count += 1

        # 2. Заполняем ограничения (Constraints)
        # Формат: (Описание, Вес, Техническое имя)
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
            ("Окно у преподавателя", 50, "teachers_gap"),
            ("Перегрузка преподавателя", 50, "teacher_overload")
        ]
        
        c_count = 0
        for description, weight, name in constraints:
            obj, created = Constraint.objects.get_or_create(
                name=name, # name теперь уникальное поле
                defaults={
                    'weight': weight,
                    'description': description
                }
            )
            if created: c_count += 1

        self.stdout.write(self.style.SUCCESS(f'Создано: {ts_count} таймслотов и {c_count} ограничений!'))